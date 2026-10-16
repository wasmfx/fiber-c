;; TODO: Should move out of fiber-c?
;;
;; To resize: adjust the number of frame(i, i+1) calls, and make the "Generator function" match the highest i+1.
;;
;; cpp examples/tiersum.wat.pp | sed '/^#/d' > examples/tiersum.wat
;; $ROOT/stack-switching/interpreter/wasm -d -i examples/tiersum.wat -o out/tiersum.wasm
;;

(module
  (type $ft-0 (func))
  (type $ct-0 (cont $ft-0))
  (type $ft-1 (func (param i32)))
  (type $ct-1 (cont $ft-1))

  (tag $tag1 (param i32))
  (tag $tag2 (param i32))
  (tag $tag3 (param i32))
  (tag $tag4 (param i32))
  (tag $tag5 (param i32))
  (tag $tag6 (param i32))
  (tag $tag7 (param i32))
  (tag $tag8 (param i32))
  (tag $tag9 (param i32))
  (tag $tag10 (param i32))

  ;; The generator function
  (func $frame3 (param $state i32) (result)
    loop $l
      ;; Calculate next value (e.g., state + 1)
      (i32.add (i32.const 1) (local.get $state))
      local.set $state

      ;; Suspend, yielding the value
      ;; Stack: [ $value ]
      local.get $state
      suspend $tag1

      local.get $state
      i32.const 100000000
      i32.lt_u
      br_if $l
    end
    ;;local.get $state
  )
  (elem declare func $frame3)

;; Function $frame2 handles $tag2 and so on. Only $consumer at the top level handles $tag1 and the innermost suspens to that.
#define frame(i, j) \
  (func $frame##i (param $state i32) (result) \
    (local $k (ref $ct-0)) \
    (i32.const 0) \
    (ref.func $frame##j) \
    (cont.new $ct-1) \
    (cont.bind $ct-1 $ct-0) \
    (local.set $k) \
    (block $suspend_handler (result i32 (ref $ct-0)) \
      (local.get $k) \
      (resume $ct-0 (on $tag##i $suspend_handler)) \
      (return) \
    ) \
    (drop) \
    (drop) \
  ) \
  (elem declare func $frame##i)

frame(2, 3)
;; frame(3, 4)
;; frame(4, 5)
;; frame(5, 6)
;; frame(6, 7)
;; frame(7, 8)
;; frame(8, 9)
;; frame(9, 10)

  (func $consumer
    (local $result i32)
    (local $k (ref $ct-0))
    i32.const 0
    ref.func $frame2
    cont.new $ct-1
    cont.bind $ct-1 $ct-0
    local.set $k

    loop $consume_loop
      block $suspend_handler (result i32 (ref $ct-0))
        local.get $k
        resume $ct-0 (on $tag1 $suspend_handler)

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
  )
  (export "_start" (func $consumer))
)