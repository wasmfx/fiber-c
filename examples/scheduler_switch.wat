(module $scheduler_switch
  (rec
    (type $ft (func (param i32 (ref null $ct))))
    ;; Continuation type of all tasks
    (type $ct (cont $ft))
  )

  (global $current_task_id (mut i32) (i32.const 0))
  (global $prev_task_id (mut i32) (i32.const 0))

  (global $result (mut i32) (i32.const 0))

  ;; Tag used to yield execution in one task and resume another one.
  (tag $yield)

  ;; Switch-return tag
  ;;(tag $switch_return)

  ;; Table to hold the continuations of the tasks, let's just have
  ;; 3 tasks for now.
  (table $task_queue 10 (ref null $ct))

  ;; Worker that increments a counter and yields
  (func $worker (param i32)
    (local $max i32)
    (local $counter i32)
    
    (local.set $max (local.get 0))

    (loop $work
      ;; Do some work (just incrementing a counter here)
      (local.tee $counter (i32.add (local.get $counter) (i32.const 1)))
      ;; Yield to the next task
      (call $yield_to_next)
      ;; Continue loop if `counter < max`
      (local.get $max)
      (i32.lt_u)
      (br_if $work)
    )
  )
  (elem declare func $worker)

  ;; Wrapper for each fiber
  (func $worker_initial_entry (type $ft)
    (local $max i32)
    (local $k (ref null $ct))

    (local.set $max (local.get 0))
    (local.set $k (local.get 1))

    ;; Set table index
    (table.set $task_queue (global.get $prev_task_id) (local.get $k))

    ;; Call the worker function with the right arguments
    (call $worker (local.get $max) )
  )
  (elem declare func $worker_initial_entry)

  ;; Determines next task to switch to directly.
  (func $yield_to_next
    (local $arg i32)
    (local $received_task (ref null $ct))

    ;; Save the current task index before switching
    (global.set $prev_task_id (global.get $current_task_id))

    ;; Determine $current_task_id
    (if (i32.lt_u (global.get $current_task_id) (i32.const 9))
        ;; Increment $current_task_id
        (then (global.set $current_task_id (i32.add (global.get $current_task_id) (i32.const 1))))
        (else (global.set $current_task_id (i32.const 0))))

    ;;(block $done
      ;; (br_if $done (ref.is_null (table.get $task_queue (global.get $current_task_id))))
      ;; Switch to the $current_task_id-th entry of the table.
      (switch $ct $yield
        ;;(local.get $arg) 
        (i32.const 10000000)
        (table.get $task_queue (global.get $current_task_id)))

      ;; If we get here, some other continuation switched directly to us.
      ;; Put it in the table at the right index
      (local.set $received_task)
      (table.set $task_queue (global.get $prev_task_id) (local.get $received_task))
      (drop)
      ;;)
    )

  ;; Initialise the table with $num_worker workers
  (func $spawn_workers (param $num_workers i32)

    ;; Temporary variable to hold the continuation reference before putting it in the table
    (local $cont (ref null $ct))
    ;; Counter for loop
    (local $i i32)

    (loop $init_table
      ;; Make a new continuation for the worker function
      (cont.new $ct (ref.func $worker_initial_entry))
      ;; Put it in the i-th index of the table
      (local.set $cont)
      (table.set $task_queue (local.get $i) (local.get $cont))
      ;; increment i
      (local.tee $i (i32.add (local.get $i) (i32.const 1)))
      ;; Continue loop if `i < $num_workers`
      (local.get $num_workers)
      (i32.le_u)
      (br_if $init_table)
    )
  )

  ;; Entry point
  (func $entry (param $num_workers i32)
    ;; Populate the task queue
    (call $spawn_workers (local.get $num_workers))
    ;; Resume the 0th worker

    (resume $ct (on $yield switch)
          (i32.const 10000000) ;; Argument passed to the worker, the max count for the loop
          (ref.null $ct)
          (table.get $task_queue (global.get $current_task_id)))

    ;; TODO: Implement switch-return stuff
    ;; (block $switch_return
    ;;   (resume $ct (on $yield switch) (on $switch_return $switch_return)
    ;;       (i32.const 3) ;; Argument passed to the worker, the max count for the loop
    ;;       (ref.null $ct)
    ;;       (table.get $task_queue (global.get $current_task_id)))
    ;;   )
  )

  (func $_start
    (block $exit
      ;; Call entry point with 9 (which spawns 10 workers)
      (call $entry (i32.const 9))
      ;; TODO: Validate result
      (global.get $result)
      (i32.const 0)
      (i32.eq)
      (br_if $exit)
      (unreachable)
    )
  )

  (export "_start" (func $_start))
)
