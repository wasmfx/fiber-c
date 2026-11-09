;; This example combines a switch-based round-robin scheduler with a simple iterating generator.
;; It demonstrates how things work when we have more than one tag. The task-yields presently only
;; happen on the outer loop of the consumer for the generator, and as a consequence all the
;; suspends are only looking up the stack by one stack segment.
(module $scheduler_and_generator
  (rec
    ;; Function type of all tasks
    (type $task-type (func (param i32 (ref null $task-cont-type))))
    ;; Continuation type of all tasks
    (type $task-cont-type (cont $task-type))
  )

  (type $vapid-func (func))
  (type $vapid-cont-type (cont $vapid-func))
  (type $generator-func-type (func (param i32)))
  (type $generator-cont-type (cont $generator-func-type))

  (global $current_task_id (mut i32) (i32.const 0))
  (global $prev_task_id (mut i32) (i32.const 0))

  (global $result (mut i32) (i32.const 0))

  ;; Tag used to switch scheduler tasks.
  (tag $thread-switch)
  ;; Tag used to yield a generator values.
  (tag $yield (param i32))

  ;; Table to hold the continuations of the tasks, let's just have
  ;; 10 tasks for now. (Wizard crashes if I set the table size to 10!)
  (table $task_queue 11 (ref null $task-cont-type))

  ;; The generator function
  (func $generator (param $state i32) (result)
    loop $l
      ;; Calculate next value (e.g., state + 1)
      (i32.add (i32.const 1) (local.get $state))
      local.set $state

      ;; Suspend, yielding the value
      ;; Stack: [ $value ]
      local.get $state
      suspend $yield

      local.get $state
      i32.const 10000000  ;; total iterations of EACH generator
      i32.lt_u
      br_if $l
    end
    ;;local.get $state
  )
  (elem declare func $generator)

  ;; $worker loops $max times, yielding to the next task each time. No data
  ;; is passed to the next task as it is.
  (func $worker (param i32)
    (local $max i32)
    (local $counter i32)
    (local $generator-k (ref null $vapid-cont-type))

    (local.set $max (local.get 0))

    (i32.const 0)
    (ref.func $generator)
    (cont.new $generator-cont-type)
    (cont.bind $generator-cont-type $vapid-cont-type)
    (local.set $generator-k)

    (loop $work
      ;; Do some work (just incrementing a counter here)
      (local.tee $counter (i32.add (local.get $counter) (i32.const 1)))

      (loop $consume_loop
        (global.set $result (i32.add (global.get $result) (i32.const 1))) ;; some simple validation.
        (block $yield_handler (result i32 (ref $vapid-cont-type))
          (resume $vapid-cont-type (on $yield $yield_handler) (local.get $generator-k))
          (return)
        )
        (local.set $generator-k)

        ;; Yield to the next task
        (call $switch-to-next-thread)
        (br $consume_loop)
      )
      ;; Fall through the $work loop (TODO: not sure how I want to go.)
      (drop)  ;; TODO: use this value
    )
  )
  (elem declare func $worker)

  ;; Entry point for each fiber: Takes an arg ($max) and, as per the switch
  ;; protocol, takes a continuation reference ($k) which needs to be stored
  ;; in the task table or else it would get lost. Calls $worker in any case.
  (func $worker_initial_entry (type $task-type)
    (local $max i32)
    (local $k (ref null $task-cont-type))

    (local.set $max (local.get 0))
    (local.set $k (local.get 1))

    ;; Set table index
    (table.set $task_queue (global.get $prev_task_id) (local.get $k))

    ;; Call the worker function with the right arguments
    (call $worker (local.get $max) )
  )
  (elem declare func $worker_initial_entry)

  ;; $switch-to-next-thread: This is really the scheduler. It maintains the global
  ;; scheduler state and yields a value to the next task in the ring.
  (func $switch-to-next-thread
    (local $arg i32) ;; unused local; I think this was intended to be a param.
    (local $received_task (ref null $task-cont-type))

    ;; Save the current task index before switching
    (global.set $prev_task_id (global.get $current_task_id))

    ;; Determine $current_task_id
    (if (i32.lt_u (global.get $current_task_id) (i32.const 9))
        ;; Increment $current_task_id
        (then (global.set $current_task_id (i32.add (global.get $current_task_id) (i32.const 1))))
        (else (global.set $current_task_id (i32.const 0))))

    ;; Switch to the $current_task_id-th entry of the table.
    (switch $task-cont-type $thread-switch
      ;;(local.get $arg)
      (i32.const 0)  ;; Passing this data to the next task, but it's ignored.
      (table.get $task_queue (global.get $current_task_id)))

    ;; Per the switch protocol, the continuation of the previous task is returned on stack,
    ;; so we need to make sure it gets into the table.
    (local.set $received_task)
    (table.set $task_queue (global.get $prev_task_id) (local.get $received_task))
    (drop)  ;; Drop the data value given to the switch.
  )

  ;; Initialise the table with $num_worker workers
  (func $spawn_workers (param $num_workers i32)
    ;; Counter for loop
    (local $i i32)

    (loop $init_table
      ;; Make a new continuation for the worker function and put it in the i-th
      ;; index of the table
      (table.set $task_queue (local.get $i) (cont.new $task-cont-type (ref.func $worker_initial_entry)))
      ;; increment i
      (local.tee $i (i32.add (local.get $i) (i32.const 1)))
      ;; Continue loop if `i < $num_workers`
      (local.get $num_workers)
      (i32.lt_u)
      (br_if $init_table)
    )
  )

  ;; Entry point
  (func $entry (param $num_workers i32)
    ;; Populate the task queue
    (call $spawn_workers (local.get $num_workers))

    ;; Resume the 0th worker
    (resume $task-cont-type (on $thread-switch switch)
          (i32.const 0) ;; Argument passed to the worker; ignored
          (ref.null $task-cont-type)
          (table.get $task_queue (global.get $current_task_id)))
  )

  (func $_start (export "_start")
    (block $exit
      ;; Do the work with 10 workers
      (call $entry (i32.const 10))

      ;; Validate result
      (global.get $result)
      (i32.const 100000001) ;; Checking that number of iterations counted across all tasks is correct. This is the number of tasks times number of generator loops. Plus one (?!).
      (i32.eq)
      (br_if $exit)
      (unreachable)
    )
  )
)
