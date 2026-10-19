(module
  ;; Fiber type: takes no resume args, yields only an i32
  (type $GenFiberF (func (param i32) (result i32)))
  (type $GenFiber (sub (fiber 0)))

  ;; The generator function
  ;; $self is automatically prepended by fiber.new, followed by the prefixed $state
  (func $gen_func (param $self (ref $GenFiber)) (param $state i32) (result i32)
    loop $l
      ;; Calculate next value (e.g., state + 1)
      (i32.add (i32.const 1) (local.get $state))
      local.set $state

      ;; Suspend, yielding the value
      ;; Stack: [ $value, (ref $GenFiber) ]
      local.get $state
      local.get $self
      fiber.suspend $GenFiber
      drop

      local.get $state
      i32.const 100000000  ;; total iterations
      i32.lt_u
      br_if $l
    end
    local.get $state
  )

  (func $consumer
    (local $f (ref $GenFiber))
    (local $result i32)

    ;; Prefix the initial state (0) and create the fiber.
    ;; The new fiber's ref is automatically prepended as the first argument to $gen_func.
    i32.const 0
    fiber.new $GenFiber $gen_func
    local.set $f

    loop $consume_loop
      block $suspend_handler (result i32)
        ;; Push fiber ref and resume
        local.get $f
        i32.const 0
        fiber.resume $GenFiber $suspend_handler

        ;; If we reach here, the generator returned (finished)
        return
      end

      ;; If we reach here, the generator suspended.
      ;; Stack contains: [ value ]
      ;; The resumer already knows `$f` is the fiber that suspended.

      ;; Process the yielded i32 value...
      local.get $result
      i32.add
      local.set $result

      br $consume_loop
    end
  )
  (export "_start" (func $consumer))
)
