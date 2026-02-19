(module $env
  ;; 1. Define and Export Memory
  ;; Syntax: (memory $name (export "export_name") initial_pages [max_pages])
  ;; 1 page = 64KB. This creates a 64KB memory exported as "memory".
  (memory $0 (export "memory") 1)

  ;; 2. Define and Export Table
  ;; Syntax: (table $name (export "export_name") initial_size [max_size] type)
  ;; This creates a table with 10 slots for function references.
  (table $__indirect_function_table (export "__indirect_function_table") 10 funcref)
)