(module
  (type $ft-0 (func))
  (type $ct-0 (cont $ft-0))
  (type $ft-1 (func (param i32)))
  (type $ct-1 (cont $ft-1))
  (tag $yield (param i32))

  ;; The generator function
  (func $gen_func (param $state i32) (result)
    loop $l
      ;; Calculate next value (e.g., state + 1)
      (i32.add (i32.const 1) (local.get $state))
      local.set $state

      ;; Suspend, yielding the value
      ;; Stack: [ $value ]
      local.get $state
      suspend $yield

      local.get $state
      i32.const 100000000  ;; total iterations
      i32.lt_u
      br_if $l
    end
    ;;local.get $state
  )
  (elem declare func $gen_func)

  (func $consumer
    (local $result i32)
    (local $k (ref $ct-0))
    ref.func $gen_func
    i32.const 0
    ref.func $gen_func
    cont.new $ct-1
    cont.bind $ct-1 $ct-0
    local.set $k

    loop $consume_loop
      block $suspend_handler (result i32 (ref $ct-0))
        local.get $k
        resume $ct-0 (on $yield $suspend_handler)

        ;; If we reach here, the generator returned (finished)
        return
      end
      local.set $k

      ;; If we reach here, the generator suspended.
      ;; Stack contains: [ value ]

      ;; Process the yielded i32 value...
      local.get $result
      i32.add
      local.set $result

      br $consume_loop
    end
    drop
  )
  (export "_start" (func $consumer))
)

