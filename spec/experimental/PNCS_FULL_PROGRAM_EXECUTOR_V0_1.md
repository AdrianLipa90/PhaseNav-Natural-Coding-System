# PNCS Full Program Executor v0.1

Status: `PURE_COMPATIBILITY_HARNESS_PASS / INTEGRATION_REPLAY_PENDING`  
Epistemic: `CHYBA`  
Mode: `READ_ONLY`  
Track: `POST_V1_LANGUAGE_ENGINEERING`

## 1. Scope

This contract opens execution only for the complete **currently admitted bounded v0.23/v0.24 program grammar**:

```text
registered IF/THEN/ELSE control root
AND THEN <registered internal route>*
RETURN <registered selector>
```

It preserves all existing semantic authorities. It introduces no new KAKU opcode and does not alter the historical v0.23, v0.24 or v0.25 receipts.

The execution chain is:

```text
verified v0.24 NativeProgramUnit
-> compile exact execution plan
-> v0.25 resident CONTROL_DISPATCH
-> registered continuation route(s)
-> terminal registered RETURN
-> deterministic full-program execution receipt
```

## 2. Reuse boundary

The control root is not reimplemented.

The executor delegates it to the existing v0.25 `PersistentProgramRuntime.dispatch_control()` boundary, which already validates:

- resident admission before and after control execution;
- exact live runtime generation;
- exact v0.20 native execution receipt;
- exact v0.22 inverse lineage;
- resident program / control Definition identity;
- `INTERNAL_TRANSFORM` control result;
- `TRUE` or `FALSE` branch truth state;
- canonical live `/dev/shm/ciel_noema` runtime.

The new executor consumes the resulting verified `ResidentDispatchReceipt`.

## 3. Program counter

The first executable program counter is instruction-level, not raw-opcode-level.

For a program containing `N` continuation routes:

```text
PC 0       CONTROL_DISPATCH
PC 1..N    CONTINUATION_ROUTE
PC N+1     RETURN
```

Every instruction binds an exact half-open span `[operator_start, operator_stop)` of the v0.24 operator schedule.

The spans must be contiguous and must cover the schedule exactly.

## 4. Control instruction

`CONTROL_DISPATCH` owns the exact existing v0.20 control Definition leaf path.

It delegates to v0.25 and yields at least:

```text
control_location
branch_truth_state
result_id
lineage_id
generation_id
resident_dispatch_id
```

No new control semantics are inferred by this layer.

## 5. Continuation instruction

Each v0.23 continuation is already a registered `INTERNAL_TRANSFORM` route reference.

Its exact operator span is:

```text
ORDER
TRANSFORM
COMPOSITION
```

Execution advances the program control location to the registered canonical target in declared program order.

A route with another route kind, a changed operator span, an unknown route reference or a schedule mismatch fails closed.

This v0.1 executor therefore executes registered internal continuation routing only. It does not open arbitrary mutation or an external effect.

## 6. RETURN execution

The final program instruction must cover exactly the final existing `RETURN` operator.

Supported v0.23 selectors are preserved:

```text
result.control_location
result.branch_truth_state
result.final_sigma_id
result.lineage_id
```

Selector/source-kind binding remains authoritative.

`result.control_location` returns the final full-program control location after admitted continuations.

`result.branch_truth_state` returns the verified v0.25 control dispatch truth state.

`result.lineage_id` returns the verified v0.22 lineage identity.

`result.final_sigma_id` requires an explicit typed binding because the v0.25 `ResidentDispatchReceipt` does not contain the final Sigma identity directly. Missing or untyped binding fails closed.

## 7. Prepared resident hot path

`compile_full_program_plan()` performs content-address and exact schedule verification once. A verified `FullProgramExecutionPlan` can then be executed through `execute_prepared_program()` without reparsing or rehashing the immutable v0.24 ProgramUnit on every resident dispatch.

The dispatch itself is still validated on every execution.

Local validation benchmark, two continuation routes, 9 repeats × 5000 executions:

```text
full compile+execute median:  ~110.84 us/program
prepared execute median:      ~30.50 us/program
executor-overhead ratio:      ~3.63x
```

This is an environment-specific software measurement of executor overhead, not a universal runtime speed claim.

## 8. Deterministic execution receipt

The receipt binds:

```text
program_id
composition_id
execution_plan_id
resident_dispatch_id
runtime_generation_id
result_id
lineage_id
branch_truth_state
ordered execution trace
return_ref_id
return_selector
return_source_kind
return_value
final_control_location
```

and content-addresses the payload as:

```text
pncs:full-program-execution:sha256:<digest>
```

Exact replay of the same verified inputs produces the same execution identity.

## 9. Boundary status

For this contract:

```text
continuation_execution_opened = true
return_execution_opened = true
full_current_bounded_program_execution = true
loops_opened = false
function_calls_opened = false
external_effects = false
free_form_nl_execution = false
static_runtime_fallback = false
```

The existing v0.26 Effect Boundary remains the only effect-authority mechanism. This executor does not inherit or create effect authorization.

## 10. Failure semantics

Execution fails closed for at least:

- v0.24 program schema or contract mismatch;
- program/composition identity mismatch;
- operator schedule/payload mismatch;
- missing terminal `RETURN`;
- altered control leaf prefix;
- continuation span other than `ORDER -> TRANSFORM -> COMPOSITION`;
- non-`INTERNAL_TRANSFORM` continuation route;
- return-reference mismatch;
- historical v0.24 execution/effect/static boundary already opened;
- non-v0.25 dispatch schema or runtime contract;
- changed v0.25 kernel scope;
- changed resident program or handle identity;
- changed v0.22 lineage contract;
- malformed result/truth/target identities;
- dispatch content-address digest mismatch;
- missing explicit typed `result.final_sigma_id` binding.

## 11. Validation evidence

Current isolated compatibility/native/spec harness:

```text
39/39 PASS
```

The harness covers compilation, exact PC/operator partitioning, zero and multiple continuations, all current return selectors, deterministic replay, route ordering, schedule tamper, program/composition content-address tamper, route-kind tamper, terminal-return tamper, historical-boundary tamper, resident-dispatch contract/digest/handle tamper, runtime delegation and prepared-plan equivalence.

`py_compile`: `PASS`.

A full repository integration replay using the concrete v0.23 `NaturalProgramComposition`, v0.24 `NativeProgramUnit` and live v0.25 resident artifacts remains a separate evidence gate. No such PASS is inferred from the compatibility harness.

The exact live NOEMA guard before final byte freeze returned `ACTIVE` with `failures=[]` and required socket enabled.

## 12. Next language gates

After exact integration replay, the next language-engineering layers are:

```text
bounded cycle / loop execution
lexical typed bindings
function activation frames
CALL / executable function RETURN
basic value and type contracts
```

Each remains separately gated.
