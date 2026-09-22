(type $ft1 (func (param) (result)))
(type $ct1 (cont $ft1))

(table $cont-table 10000 (ref null $ct1))

(func $null-func
  )

(elem declare func $null-func)

(func $cont-new-loop
    (local $i i32)
    (local $k (ref $ct1))
    (local.set $i (i32.const 9999))
    (loop $loop
        (cont.new $ct1 (ref.func $null-func))
        (local.set $k)
        (table.set $cont-table (local.get $i) (local.get $k))

        (local.tee $i (i32.sub (local.get $i) (i32.const 1)))
        (br_if $loop)
    )
    (local.set $i (i32.const 9999))
    (loop $loop
        (table.get $cont-table (local.get $i))
        (resume $ct1)
        (local.tee $i (i32.sub (local.get $i) (i32.const 1)))
        (br_if $loop)
    )
)

(func $_start
  (local $j i32)
  (local.set $j (i32.const 1000))
  (loop $many-times
    (call $cont-new-loop)
    (local.tee $j (i32.sub (local.get $j) (i32.const 1)))
    (br_if $many-times)
))

(export "_start" (func $_start))

;; To run:
;; /opt/wasmfx/wasmfxtime/target/release/wasmtime -W stack-switching,function-references -W total-stacks=10000 fiber-c/examples/minic10m.wat