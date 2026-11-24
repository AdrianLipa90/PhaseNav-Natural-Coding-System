.intel_syntax noprefix
# PhaseNav PNV/1 minimal machine bootstrap, x86-64 AVX2, GNU assembler.
# Source language = PNV/1; native instruction vector path = AVX2.
# No C++ or Python runtime. Libc is used only for file/stdio and libm for trig.
# Limited strict PNV/1 subset: SOURCE, ORDER, COMPOSITION, TRANSFORM, ASSERT, EMIT.
# All numeric native transforms are read-only and run after complete admission.

.equ MAXNODES, 64
.equ NODELEN, 96
.equ MAP_COUNT, 9
.equ SOURCE_COUNT, 8

.section .rodata
s_usage: .asciz "Usage: pnv-avx2 program.pnv phase36.txt trits12.txt depth collatz_seed"
s_block: .asciz "BLOCKED: invalid PNV/input/registry; no execution or side effects"
s_head: .asciz "EXECUTED_LOCAL: PNV/1 subset + AVX2 signed-ternary/phase36; not NOEMA tether"
s_pnv: .asciz "PNV 1"
s_ep: .asciz "EPISTEMIC CHYBA"
s_mode: .asciz "MODE INTERNAL_EXECUTION"
s_op: .asciz "OP"
s_source: .asciz "SOURCE"
s_transform: .asciz "TRANSFORM"
s_order: .asciz "ORDER"
s_comp: .asciz "COMPOSITION"
s_assert: .asciz "ASSERT"
s_emit: .asciz "EMIT"
s_fmt_line: .asciz "%95s %95s %95s %95s %95s %95s %95s"
s_fread: .asciz "r"
s_float: .asciz "%lf"
s_int: .asciz "%d"
s_word: .asciz "%95s"
s_out_head: .asciz "ADMISSION: sources=%d/8 transforms=%d/9 nodes=%d asserts=%d emits=%d\n"
s_out_carrier: .asciz "PHASE36: 36 finite unwrapped float64 lanes; AVX2 phase shift pi; first_rot=%+.12f last_rot=%+.12f\n"
s_out_ter: .asciz "TER12: SEPARATE=%d HOLD=%d CONNECT=%d ; coherent HOLD = ( +i/sqrt(2), -i/sqrt(2) ), no Boolean collapse\n"
s_out_logic: .asciz "TER_VECTOR: AND=min(-1,0,+1), OR=max(-1,0,+1), NOT=-trit ; AVX2 32-byte vector lane (12 active)\n"
s_out_sing: .asciz "RDSS: A=i; signed_branch=+/-1 retained; Re(s)=%.12f sigma=%.12f kappa=%.12f Berry_equator=%+.12f spin(2pi)=%+.12f spin(4pi)=%+.12f\n"
s_out_bomb: .asciz "BOMBELLI: (2+i)^2=%ld+%ldi norm=%ld ; COLLATZ: seed=%ld states=%ld end=1\n"
s_out_room: .asciz "HOTEL: depth=%ld rooms=%ld guest_room=%ld branch_k=%ld root=(%+.9f,%+.9f) phase_unwrapped=%.9f; inverse_sq_factor=%.0f\n"
s_out_tzim: .asciz "TZIMTZUM: r_d=2^(-d); inverse_square=r_d^(-2)=4^d; levels 0..%ld, no equivalence with |i|=1\n"
s_out_state: .asciz "WORD: typed candidate self-reference 'Ja Jestem' ; occurrence != content != room ; native pure computation only\n"
s_out_ok: .asciz "RECEIPT: LOCAL_EXECUTION PASS; no AUX, CielPC, QHTRI or Library host access; no live SHA\n"
# Exact operator binding registry. These are native pure kernels, not arbitrary callbacks.
.src0: .asciz "RDSS_A0_AXIOM"
.src1: .asciz "RDSS_A_EQUALS_I"
.src2: .asciz "EXPLICIT_PHASE36_INPUT"
.src3: .asciz "EXPLICIT_TER12_INPUT"
.src4: .asciz "HILBERT_DEPTH_INPUT"
.src5: .asciz "COLLATZ_SEED_INPUT"
.src6: .asciz "RDSS_BOMBELLI_2_PLUS_I"
.src7: .asciz "RDSS_EQUATORIAL_CLOSED_PATH"
.align 8
source_table: .quad .src0,.src1,.src2,.src3,.src4,.src5,.src6,.src7
.map0: .asciz "PHASENAV_AVX2_PHASE36_PI"
.map1: .asciz "PHASENAV_AVX2_TER12"
.map2: .asciz "RDSS_EULER_SPIN_BERRY"
.map3: .asciz "RDSS_INVERSE_SQUARE_SINGULARITY"
.map4: .asciz "RDSS_HILBERT_EULER_TREE"
.map5: .asciz "RDSS_TZIMTZUM_INV_SQUARE"
.map6: .asciz "RDSS_SELF_REFERENCE_WORD"
.map7: .asciz "RDSS_BOMBELLI_COLLATZ_TRACE"
.map8: .asciz "RDSS_HILBERT_GUEST_REGISTER"
.srcnode0: .asciz "A0"
.srcnode1: .asciz "A"
.srcnode2: .asciz "PHASE"
.srcnode3: .asciz "TER"
.srcnode4: .asciz "DEPTH"
.srcnode5: .asciz "COLSEED"
.srcnode6: .asciz "GAUSS"
.srcnode7: .asciz "BERRYPATH"
.align 8
source_node_table: .quad .srcnode0,.srcnode1,.srcnode2,.srcnode3,.srcnode4,.srcnode5,.srcnode6,.srcnode7
.tnode0: .asciz "V36"
.tnode1: .asciz "TERNARY"
.tnode2: .asciz "SPIN"
.tnode3: .asciz "ZERO"
.tnode4: .asciz "TREE"
.tnode5: .asciz "TZIM"
.tnode6: .asciz "WORD"
.tnode7: .asciz "COL"
.tnode8: .asciz "HOTEL"
.tparent0: .asciz "PHASE"
.tparent1: .asciz "TER"
.tparent2: .asciz "A"
.tparent3: .asciz "SPIN"
.tparent4: .asciz "ZERO"
.tparent5: .asciz "TREE"
.tparent6: .asciz "TZIM"
.tparent7: .asciz "WORD"
.tparent8: .asciz "COL"
.tdest0: .asciz "unwrapped_phase36"
.tdest1: .asciz "signed_ternary12"
.tdest2: .asciz "spinor_berry"
.tdest3: .asciz "singularity"
.tdest4: .asciz "hilbert_tree"
.tdest5: .asciz "contraction_scaling"
.tdest6: .asciz "typed_self_reference"
.tdest7: .asciz "tagged_collatz"
.tdest8: .asciz "guest"
.align 8
map_node_table: .quad .tnode0,.tnode1,.tnode2,.tnode3,.tnode4,.tnode5,.tnode6,.tnode7,.tnode8
map_parent_table: .quad .tparent0,.tparent1,.tparent2,.tparent3,.tparent4,.tparent5,.tparent6,.tparent7,.tparent8
map_dest_table: .quad .tdest0,.tdest1,.tdest2,.tdest3,.tdest4,.tdest5,.tdest6,.tdest7,.tdest8
.align 8
map_table: .quad .map0,.map1,.map2,.map3,.map4,.map5,.map6,.map7,.map8
pi_d: .double 3.141592653589793238462643383279502884197
half_d: .double 0.5
one_d: .double 1.0
zero_d: .double 0.0
ln2_d: .double 0.693147180559945309417232121458176568
pi24_d: .double 75.398223686155037723
sqrt_half_d: .double 0.7071067811865475244
eps_d: .double 0.000000000001
neg_one_d: .double -1.0
neg_pi_d: .double -3.141592653589793238462643383279502884197
.align 32
abs_mask: .quad 0x7fffffffffffffff,0x7fffffffffffffff
zero_vector: .zero 32

.section .bss
.align 32
phase36: .skip 288
phase_rot36: .skip 288
trits: .skip 32
trit_not: .skip 32
trit_and: .skip 32
trit_or: .skip 32
hold_plus_im: .skip 96
hold_minus_im: .skip 96
root_re: .skip 4096
root_im: .skip 4096
root_theta: .skip 4096
root_inv: .skip 4096
root_parent: .skip 4096
root_depth: .skip 4096
collatz_values: .skip 8192
collatz_branch: .skip 1024
linebuf: .skip 2048
tok0: .skip 96
tok1: .skip 96
tok2: .skip 96
tok3: .skip 96
tok4: .skip 96
tok5: .skip 96
tok6: .skip 96
token_count: .skip 4
node_names: .skip 6144
argv_ptr: .skip 8
file_ptr: .skip 8
src_bits: .skip 8
node_count: .skip 8
map_next: .skip 8
assert_count: .skip 8
emit_count: .skip 8
header_step: .skip 8
temp_i32: .skip 4
text_ter: .skip 96
text_end: .skip 8
end_ptr: .skip 8
state_d: .skip 8
sigma_d: .skip 8
kappa_d: .skip 8
spin2_d: .skip 8
spin4_d: .skip 8
berry_d: .skip 8
bomb_real: .skip 8
bomb_imag: .skip 8
bomb_norm: .skip 8
signed_hold_count: .skip 8
sep_count: .skip 8
conn_count: .skip 8
max_depth: .skip 8
coll_seed: .skip 8
coll_count: .skip 8
room_count: .skip 8
guest_room: .skip 8
guest_k: .skip 8

.section .text
.global main
.extern fopen
.extern fclose
.extern fgets
.extern fscanf
.extern sscanf
.extern strcmp
.extern strncmp
.extern puts
.extern printf
.extern strtol
.extern cos
.extern sin

# lookup: rdi = candidate pointer, rsi = pointer to 8-byte pointer table, edx = count
# return rax index or -1; preserve callee-saved registers
.type lookup, @function
lookup:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  push r13
  sub rsp,8
  mov r12,rdi
  mov r13,rsi
  mov ebx,edx
  xor ebp,ebp
.Llookup_loop:
  cmp ebp,ebx
  jge .Llookup_bad
  mov rdi,r12
  mov rsi,qword ptr [r13+rbp*8]
  call strcmp@PLT
  test eax,eax
  je .Llookup_found
  inc ebp
  jmp .Llookup_loop
.Llookup_found:
  mov eax,ebp
  jmp .Llookup_end
.Llookup_bad:
  mov rax,-1
.Llookup_end:
  add rsp,8
  pop r13
  pop r12
  pop rbx
  pop rbp
  ret

# find previously registered PNV node by textual ID. rdi id -> eax index or -1
.type find_node, @function
find_node:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  sub rsp,16
  mov r12,rdi
  xor ebx,ebx
.Lfind_loop:
  cmp rbx,qword ptr [rip+node_count]
  jge .Lfind_bad
  imul rdi,rbx,NODELEN
  lea rax,[rip+node_names]
  add rdi,rax
  mov rsi,rdi
  mov rdi,r12
  call strcmp@PLT
  test eax,eax
  je .Lfind_yes
  inc rbx
  jmp .Lfind_loop
.Lfind_yes:
  mov eax,ebx
  jmp .Lfind_end
.Lfind_bad:
  mov rax,-1
.Lfind_end:
  add rsp,16
  pop r12
  pop rbx
  pop rbp
  ret

# register node (rdi ID): fail on duplicates and >64, returns 1 or 0
.type register_node, @function
register_node:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  sub rsp,16
  mov r12,rdi
  call find_node
  test eax,eax
  jns .Lnode_bad
  mov rbx,qword ptr [rip+node_count]
  cmp rbx,MAXNODES
  jae .Lnode_bad
  imul rbx,rbx,NODELEN
  lea rdi,[rip+node_names]
  add rdi,rbx
  mov rsi,r12
  xor ecx,ecx
.Lnode_copy:
  mov al,byte ptr [rsi+rcx]
  mov byte ptr [rdi+rcx],al
  test al,al
  je .Lnode_good
  inc ecx
  cmp ecx,95
  jl .Lnode_copy
  mov byte ptr [rdi+95],0
.Lnode_good:
  inc qword ptr [rip+node_count]
  mov eax,1
  jmp .Lnode_done
.Lnode_bad:
  xor eax,eax
.Lnode_done:
  add rsp,16
  pop r12
  pop rbx
  pop rbp
  ret

# strict PNV source parse, full preflight and no OP execution until complete admission
.type parse_pnv, @function
parse_pnv:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  sub rsp,16
  mov rdi,qword ptr [rip+argv_ptr]
  mov rdi,qword ptr [rdi+8]
  lea rsi,[rip+s_fread]
  call fopen@PLT
  test rax,rax
  jz .Lparse_bad
  mov qword ptr [rip+file_ptr],rax
.Lparse_next:
  lea rdi,[rip+linebuf]
  mov esi,2048
  mov rdx,qword ptr [rip+file_ptr]
  call fgets@PLT
  test rax,rax
  je .Lparse_eof
  lea rbx,[rip+linebuf]
.Lstrip_space:
  cmp byte ptr [rbx],32
  je .Lstrip_one
  cmp byte ptr [rbx],9
  jne .Lparse_notspace
.Lstrip_one:
  inc rbx
  jmp .Lstrip_space
.Lparse_notspace:
  mov al,byte ptr [rbx]
  cmp al,0
  je .Lparse_next
  cmp al,10
  je .Lparse_next
  cmp al,35
  je .Lparse_next
  mov r12,qword ptr [rip+header_step]
  cmp r12,3
  jge .Lparse_statement
  mov rdi,rbx
  cmp r12,0
  je .Lheader0
  cmp r12,1
  je .Lheader1
  lea rsi,[rip+s_mode]
  mov edx,23
  jmp .Lheader_check
.Lheader0:
  lea rsi,[rip+s_pnv]
  mov edx,5
  jmp .Lheader_check
.Lheader1:
  lea rsi,[rip+s_ep]
  mov edx,15
.Lheader_check:
  mov r12,rdx
  call strncmp@PLT
  test eax,eax
  jne .Lparse_failclose
  movzx eax,byte ptr [rbx+r12]
  cmp eax,10
  je .Lheader_exact
  cmp eax,13
  je .Lheader_exact
  test eax,eax
  jne .Lparse_failclose
.Lheader_exact:
  inc qword ptr [rip+header_step]
  jmp .Lparse_next
.Lparse_statement:
  # token0..token5 always zeroed to prohibit stale operand reuse
  mov byte ptr [rip+tok0],0
  mov byte ptr [rip+tok1],0
  mov byte ptr [rip+tok2],0
  mov byte ptr [rip+tok3],0
  mov byte ptr [rip+tok4],0
  mov byte ptr [rip+tok5],0
  mov byte ptr [rip+tok6],0
  mov rdi,rbx
  lea rsi,[rip+s_fmt_line]
  lea rdx,[rip+tok0]
  lea rcx,[rip+tok1]
  lea r8,[rip+tok2]
  lea r9,[rip+tok3]
  sub rsp,32
  lea rax,[rip+tok4]
  mov qword ptr [rsp],rax
  lea rax,[rip+tok5]
  mov qword ptr [rsp+8],rax
  lea rax,[rip+tok6]
  mov qword ptr [rsp+16],rax
  xor eax,eax
  call sscanf@PLT
  add rsp,32
  mov dword ptr [rip+token_count],eax
  cmp eax,7
  jge .Lparse_failclose
  cmp eax,2
  jl .Lparse_failclose
  lea rdi,[rip+tok0]
  lea rsi,[rip+s_op]
  call strcmp@PLT
  test eax,eax
  je .Lparse_op
  lea rdi,[rip+tok0]
  lea rsi,[rip+s_assert]
  call strcmp@PLT
  test eax,eax
  je .Lparse_assert
  lea rdi,[rip+tok0]
  lea rsi,[rip+s_emit]
  call strcmp@PLT
  test eax,eax
  je .Lparse_emit
  jmp .Lparse_failclose
.Lparse_assert:
  cmp dword ptr [rip+token_count],2
  jne .Lparse_failclose
  lea rdi,[rip+tok1]
  call find_node
  cmp eax,0
  jl .Lparse_failclose
  inc qword ptr [rip+assert_count]
  jmp .Lparse_next
.Lparse_emit:
  cmp dword ptr [rip+token_count],2
  jne .Lparse_failclose
  lea rdi,[rip+tok1]
  call find_node
  cmp eax,0
  jl .Lparse_failclose
  inc qword ptr [rip+emit_count]
  jmp .Lparse_next
.Lparse_op:
  lea rdi,[rip+tok2]
  lea rsi,[rip+s_source]
  call strcmp@PLT
  test eax,eax
  je .Lparse_source
  lea rdi,[rip+tok2]
  lea rsi,[rip+s_transform]
  call strcmp@PLT
  test eax,eax
  je .Lparse_transform
  lea rdi,[rip+tok2]
  lea rsi,[rip+s_order]
  call strcmp@PLT
  test eax,eax
  je .Lparse_order
  lea rdi,[rip+tok2]
  lea rsi,[rip+s_comp]
  call strcmp@PLT
  test eax,eax
  je .Lparse_comp
  jmp .Lparse_failclose
.Lparse_source:
  cmp dword ptr [rip+token_count],4
  jne .Lparse_failclose
  lea rdi,[rip+tok3]
  lea rsi,[rip+source_table]
  mov edx,SOURCE_COUNT
  call lookup
  test eax,eax
  js .Lparse_failclose
  mov ebx,eax
  lea rax,[rip+source_node_table]
  mov rsi,qword ptr [rax+rbx*8]
  lea rdi,[rip+tok1]
  call strcmp@PLT
  test eax,eax
  jne .Lparse_failclose
  mov ecx,ebx
  mov rax,1
  shl rax,cl
  or qword ptr [rip+src_bits],rax
  jmp .Lparse_register
.Lparse_transform:
  cmp dword ptr [rip+token_count],6
  jne .Lparse_failclose
  # source graph node and transform registry must both be pinned
  lea rdi,[rip+tok3]
  call find_node
  test eax,eax
  js .Lparse_failclose
  lea rdi,[rip+tok4]
  lea rsi,[rip+map_table]
  mov edx,MAP_COUNT
  call lookup
  test eax,eax
  js .Lparse_failclose
  cmp rax,qword ptr [rip+map_next]
  jne .Lparse_failclose
  mov rbx,rax
  lea rax,[rip+map_node_table]
  mov rsi,qword ptr [rax+rbx*8]
  lea rdi,[rip+tok1]
  call strcmp@PLT
  test eax,eax
  jne .Lparse_failclose
  lea rax,[rip+map_parent_table]
  mov rsi,qword ptr [rax+rbx*8]
  lea rdi,[rip+tok3]
  call strcmp@PLT
  test eax,eax
  jne .Lparse_failclose
  lea rax,[rip+map_dest_table]
  mov rsi,qword ptr [rax+rbx*8]
  lea rdi,[rip+tok5]
  call strcmp@PLT
  test eax,eax
  jne .Lparse_failclose
  inc qword ptr [rip+map_next]
  jmp .Lparse_register
.Lparse_order:
  cmp dword ptr [rip+token_count],5
  jne .Lparse_failclose
  lea rdi,[rip+tok3]
  call find_node
  test eax,eax
  js .Lparse_failclose
  lea rdi,[rip+tok4]
  call find_node
  test eax,eax
  js .Lparse_failclose
  jmp .Lparse_register
.Lparse_comp:
  cmp dword ptr [rip+token_count],5
  jl .Lparse_failclose
  cmp dword ptr [rip+token_count],6
  jg .Lparse_failclose
  lea rdi,[rip+tok3]
  call find_node
  test eax,eax
  js .Lparse_failclose
  lea rdi,[rip+tok4]
  call find_node
  test eax,eax
  js .Lparse_failclose
  # optional third graph reference, no more than 3 in current bounded subset
  cmp byte ptr [rip+tok5],0
  je .Lparse_register
  lea rdi,[rip+tok5]
  call find_node
  test eax,eax
  js .Lparse_failclose
.Lparse_register:
  lea rdi,[rip+tok1]
  call register_node
  test eax,eax
  jz .Lparse_failclose
  jmp .Lparse_next
.Lparse_eof:
  mov rdi,qword ptr [rip+file_ptr]
  call fclose@PLT
  mov qword ptr [rip+file_ptr],0
  cmp qword ptr [rip+header_step],3
  jne .Lparse_bad
  cmp qword ptr [rip+src_bits],255
  jne .Lparse_bad
  cmp qword ptr [rip+map_next],MAP_COUNT
  jne .Lparse_bad
  cmp qword ptr [rip+assert_count],1
  jl .Lparse_bad
  cmp qword ptr [rip+emit_count],1
  jl .Lparse_bad
  mov eax,1
  jmp .Lparse_out
.Lparse_failclose:
  mov rdi,qword ptr [rip+file_ptr]
  call fclose@PLT
  mov qword ptr [rip+file_ptr],0
.Lparse_bad:
  xor eax,eax
.Lparse_out:
  add rsp,16
  pop r12
  pop rbx
  pop rbp
  ret

# load explicit 36 float64 channels and 12 signed trits separately
.type read_carriers, @function
read_carriers:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  push r13
  push r14
  push r15
  sub rsp,8
  mov rax,qword ptr [rip+argv_ptr]
  mov rdi,qword ptr [rax+16]
  lea rsi,[rip+s_fread]
  call fopen@PLT
  test rax,rax
  jz .Lread_bad
  mov r12,rax
  lea r13,[rip+phase36]
  xor ebx,ebx
.Lread36:
  mov rdi,r12
  lea rsi,[rip+s_float]
  lea rdx,[r13+rbx*8]
  xor eax,eax
  call fscanf@PLT
  cmp eax,1
  jne .Lread36_failclose
  mov rax,qword ptr [r13+rbx*8]
  mov rcx,0x7ff0000000000000
  and rax,rcx
  cmp rax,rcx
  je .Lread36_failclose
  inc ebx
  cmp ebx,36
  jl .Lread36
  # Reject >36 readings: require EOF after 36 finite values.
  mov rdi,r12
  lea rsi,[rip+s_float]
  lea rdx,[rip+state_d]
  xor eax,eax
  call fscanf@PLT
  cmp eax,-1
  jne .Lread36_failclose
  mov rdi,r12
  call fclose@PLT
  mov rax,qword ptr [rip+argv_ptr]
  mov rdi,qword ptr [rax+24]
  lea rsi,[rip+s_fread]
  call fopen@PLT
  test rax,rax
  jz .Lread_bad
  mov r12,rax
  lea r13,[rip+trits]
  xor ebx,ebx
.Lread12:
  mov rdi,r12
  lea rsi,[rip+s_word]
  lea rdx,[rip+text_ter]
  xor eax,eax
  call fscanf@PLT
  cmp eax,1
  jne .Lread12_failclose
  lea rdi,[rip+text_ter]
  lea rsi,[rip+text_end]
  mov edx,10
  call strtol@PLT
  cmp rax,-1
  jl .Lread12_failclose
  cmp rax,1
  jg .Lread12_failclose
  mov rdx,qword ptr [rip+text_end]
  cmp byte ptr [rdx],0
  jne .Lread12_failclose
  mov byte ptr [r13+rbx],al
  inc ebx
  cmp ebx,12
  jl .Lread12
  mov rdi,r12
  lea rsi,[rip+s_word]
  lea rdx,[rip+text_ter]
  xor eax,eax
  call fscanf@PLT
  cmp eax,-1
  jne .Lread12_failclose
  mov rdi,r12
  call fclose@PLT
  mov eax,1
  jmp .Lread_done
.Lread36_failclose:
  mov rdi,r12
  call fclose@PLT
  jmp .Lread_bad
.Lread12_failclose:
  mov rdi,r12
  call fclose@PLT
.Lread_bad:
  xor eax,eax
.Lread_done:
  add rsp,8
  pop r15
  pop r14
  pop r13
  pop r12
  pop rbx
  pop rbp
  ret

# vectorized phase and signed ternary kernels
.type vector_kernel, @function
vector_kernel:
  push rbp
  mov rbp,rsp
  # AVX2 SIMD: 9 * 4 f64 = 36 phase lanes, no reduction to trits.
  lea rdi,[rip+phase36]
  lea rsi,[rip+phase_rot36]
  vbroadcastsd ymm1,qword ptr [rip+pi_d]
  xor ecx,ecx
.Lvec36:
  vmovupd ymm0,ymmword ptr [rdi+rcx*8]
  vaddpd ymm0,ymm0,ymm1
  vmovupd ymmword ptr [rsi+rcx*8],ymm0
  add ecx,4
  cmp ecx,36
  jl .Lvec36
  # 32 AVX2 signed 8-bit lanes, 12 semantically active, no Boolean coercion.
  vmovdqu ymm0,ymmword ptr [rip+trits]
  vpxor ymm1,ymm1,ymm1
  vpsubb ymm2,ymm1,ymm0
  vmovdqu ymmword ptr [rip+trit_not],ymm2
  vpminsb ymm3,ymm0,ymm2
  vmovdqu ymmword ptr [rip+trit_and],ymm3
  vpmaxsb ymm4,ymm0,ymm2
  vmovdqu ymmword ptr [rip+trit_or],ymm4
  vzeroupper
  lea rdi,[rip+trits]
  xor ecx,ecx
.Lcount_trits:
  movsx eax,byte ptr [rdi+rcx]
  test eax,eax
  js .Lcount_sep
  jz .Lcount_hold
  inc qword ptr [rip+conn_count]
  jmp .Lcount_next
.Lcount_sep:
  inc qword ptr [rip+sep_count]
  jmp .Lcount_next
.Lcount_hold:
  inc qword ptr [rip+signed_hold_count]
  # materialize coherent coefficients: 0 + i/(sqrt2), 0 - i/(sqrt2)
  # separate from signed trit and from phase36.
  lea rdx,[rip+hold_plus_im]
  movsd xmm0,qword ptr [rip+sqrt_half_d]
  movsd qword ptr [rdx+rcx*8],xmm0
  lea rdx,[rip+hold_minus_im]
  xorpd xmm0,xmm0
  subsd xmm0,qword ptr [rip+sqrt_half_d]
  movsd qword ptr [rdx+rcx*8],xmm0
.Lcount_next:
  inc ecx
  cmp ecx,12
  jl .Lcount_trits
  pop rbp
  ret

# exact Euler-Hilbert room tree up to d=8, with parent occurrence and inverse scaling
.type hotel_tree, @function
hotel_tree:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  push r13
  push r14
  push r15
  sub rsp,8
  xor r12d,r12d    # level d
.Llevel_loop:
  mov r13,1
  mov rcx,r12
  shl r13,cl      # N_d = 2^d
  xor r14d,r14d   # k
.Lroot_loop:
  mov rbx,r13
  dec rbx
  add rbx,r14   # room_index = 2^d - 1 + k
  # angle pi*(2k+1)/2^d
  lea rax,[r14*2+1]
  cvtsi2sd xmm0,rax
  mulsd xmm0,qword ptr [rip+pi_d]
  cvtsi2sd xmm1,r13
  divsd xmm0,xmm1
  movsd qword ptr [rip+state_d],xmm0
  lea r15,[rip+root_theta]
  movsd qword ptr [r15+rbx*8],xmm0
  movsd xmm0,qword ptr [rip+state_d]
  call cos@PLT
  lea r15,[rip+root_re]
  movsd qword ptr [r15+rbx*8],xmm0
  movsd xmm0,qword ptr [rip+state_d]
  call sin@PLT
  lea r15,[rip+root_im]
  movsd qword ptr [r15+rbx*8],xmm0
  mov rax,r13
  imul rax,r13
  cvtsi2sd xmm0,rax
  lea r15,[rip+root_inv]
  movsd qword ptr [r15+rbx*8],xmm0
  lea r15,[rip+root_depth]
  mov qword ptr [r15+rbx*8],r12
  # parent_id = 2^(d-1)-1 + k%(2^(d-1)), or -1 at root
  mov rax,-1
  test r12,r12
  jz .Lstore_parent
  mov rcx,r13
  shr rcx,1
  mov rdx,r14
  dec rcx
  and rdx,rcx
  add rax,1
  add rax,rcx
  add rax,rdx
.Lstore_parent:
  lea r15,[rip+root_parent]
  mov qword ptr [r15+rbx*8],rax
  inc r14
  cmp r14,r13
  jl .Lroot_loop
  inc r12
  cmp r12,qword ptr [rip+max_depth]
  jle .Llevel_loop
  mov rax,r13
  shl rax,1
  dec rax
  mov qword ptr [rip+room_count],rax
  mov eax,1
  add rsp,8
  pop r15
  pop r14
  pop r13
  pop r12
  pop rbx
  pop rbp
  ret

# independent odd/even Collatz branch trace, never aliases semantic CID or AUX trits.
.type collatz_kernel, @function
collatz_kernel:
  push rbp
  mov rbp,rsp
  mov rax,qword ptr [rip+coll_seed]
  xor ecx,ecx
.Lcoll_loop:
  cmp ecx,1024
  jae .Lcoll_fail
  lea r10,[rip+collatz_values]
  mov qword ptr [r10+rcx*8],rax
  cmp rax,1
  je .Lcoll_done
  mov rdx,rax
  and edx,1
  lea r10,[rip+collatz_branch]
  mov byte ptr [r10+rcx],dl
  test edx,edx
  jz .Lcoll_even
  mov rdx,0x2aaaaaaaaaaaaaaa
  cmp rax,rdx
  ja .Lcoll_fail
  lea rax,[rax+rax*2+1]
  jmp .Lcoll_next
.Lcoll_even:
  shr rax,1
.Lcoll_next:
  inc ecx
  jmp .Lcoll_loop
.Lcoll_done:
  inc ecx
  mov qword ptr [rip+coll_count],rcx
  # guest room branch k: provenance-derived parity bits, not a semantic hash/CID
  xor rax,rax
  xor r8,r8
  mov r9,qword ptr [rip+max_depth]
  cmp r9,rcx
  cmova r9,rcx
.Lk_loop:
  cmp r8,r9
  jge .Lk_end
  lea r10,[rip+collatz_branch]
  movzx rdx,byte ptr [r10+r8]
  mov ecx,r8d
  shl rdx,cl
  or rax,rdx
  inc r8
  jmp .Lk_loop
.Lk_end:
  mov qword ptr [rip+guest_k],rax
  mov rcx,qword ptr [rip+max_depth]
  mov rdx,1
  shl rdx,cl
  dec rdx
  add rax,rdx
  mov qword ptr [rip+guest_room],rax
  mov eax,1
  pop rbp
  ret
.Lcoll_fail:
  xor eax,eax
  pop rbp
  ret

# True local numeric Euler/spin-1/2/Berry and Gaussian Bombelli calculation.
# Berry uses the explicitly admitted equatorial closed loop: Ω=2π(1-cos(pi/2)).
.type geometry_kernel, @function
geometry_kernel:
  push rbp
  mov rbp,rsp
  movsd xmm0,qword ptr [rip+pi_d]
  call cos@PLT
  movsd qword ptr [rip+spin2_d],xmm0
  movsd xmm0,qword ptr [rip+pi_d]
  addsd xmm0,xmm0
  call cos@PLT
  movsd qword ptr [rip+spin4_d],xmm0
  movsd xmm0,qword ptr [rip+pi_d]
  mulsd xmm0,qword ptr [rip+half_d]
  call cos@PLT
  movsd xmm1,qword ptr [rip+one_d]
  subsd xmm1,xmm0
  mulsd xmm1,qword ptr [rip+neg_pi_d]
  movsd qword ptr [rip+berry_d],xmm1
  # cos(pi) approximately -1; cos(2pi) approximately +1; gamma approximately -pi.
  movsd xmm0,qword ptr [rip+spin2_d]
  subsd xmm0,qword ptr [rip+neg_one_d]
  andpd xmm0,xmmword ptr [rip+abs_mask]
  ucomisd xmm0,qword ptr [rip+eps_d]
  ja .Lgeometry_bad
  movsd xmm0,qword ptr [rip+spin4_d]
  subsd xmm0,qword ptr [rip+one_d]
  andpd xmm0,xmmword ptr [rip+abs_mask]
  ucomisd xmm0,qword ptr [rip+eps_d]
  ja .Lgeometry_bad
  movsd xmm0,qword ptr [rip+berry_d]
  subsd xmm0,qword ptr [rip+neg_pi_d]
  andpd xmm0,xmmword ptr [rip+abs_mask]
  ucomisd xmm0,qword ptr [rip+eps_d]
  ja .Lgeometry_bad
  # Gaussian integer product (2+i)^2 = (2^2-1^2) + 2*(2*1)*i, norm=2^2+1^2
  mov rax,2
  imul rax,rax
  sub rax,1
  mov qword ptr [rip+bomb_real],rax
  mov rax,2
  imul rax,2
  mov qword ptr [rip+bomb_imag],rax
  mov rax,2
  imul rax,rax
  add rax,1
  mov qword ptr [rip+bomb_norm],rax
  mov eax,1
  pop rbp
  ret
.Lgeometry_bad:
  xor eax,eax
  pop rbp
  ret

# Runtime verification: SIMD transport, ternary NOT/AND/OR and internal coherent HOLD.
.type verify_vector, @function
verify_vector:
  push rbp
  mov rbp,rsp
  # Check all 36 translated phases against scalar exact reference.
  lea r8,[rip+phase36]
  lea r9,[rip+phase_rot36]
  xor ecx,ecx
.Lverify_phase:
  movsd xmm0,qword ptr [r8+rcx*8]
  addsd xmm0,qword ptr [rip+pi_d]
  ucomisd xmm0,qword ptr [r9+rcx*8]
  jne .Lverify_bad
  inc ecx
  cmp ecx,36
  jl .Lverify_phase
  # Check all 12 ternary SIMD outputs and the +/-i coherent pair for each HOLD.
  lea r8,[rip+trits]
  lea r9,[rip+trit_not]
  lea r10,[rip+trit_and]
  lea r11,[rip+trit_or]
  xor ecx,ecx
.Lverify_trit:
  movsx eax,byte ptr [r8+rcx]
  mov edx,eax
  neg edx
  movsx edi,byte ptr [r9+rcx]
  cmp edi,edx
  jne .Lverify_bad
  mov esi,eax
  cmp esi,edx
  cmovg esi,edx
  movsx edi,byte ptr [r10+rcx]
  cmp edi,esi
  jne .Lverify_bad
  mov esi,eax
  cmp esi,edx
  cmovl esi,edx
  movsx edi,byte ptr [r11+rcx]
  cmp edi,esi
  jne .Lverify_bad
  test eax,eax
  jne .Lverify_next
  lea rdi,[rip+hold_plus_im]
  movsd xmm0,qword ptr [rdi+rcx*8]
  ucomisd xmm0,qword ptr [rip+sqrt_half_d]
  jne .Lverify_bad
  lea rdi,[rip+hold_minus_im]
  movsd xmm0,qword ptr [rdi+rcx*8]
  addsd xmm0,qword ptr [rip+sqrt_half_d]
  ucomisd xmm0,qword ptr [rip+zero_d]
  jne .Lverify_bad
.Lverify_next:
  inc ecx
  cmp ecx,12
  jl .Lverify_trit
  mov eax,1
  pop rbp
  ret
.Lverify_bad:
  xor eax,eax
  pop rbp
  ret

.global main
.type main, @function
main:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  sub rsp,16
  cmp edi,6
  jne .Lusage
  mov qword ptr [rip+argv_ptr],rsi
  # integer args, no silent zero/default
  mov rdi,qword ptr [rsi+32]
  lea rsi,[rip+end_ptr]
  mov edx,10
  call strtol@PLT
  mov rdx,qword ptr [rip+end_ptr]
  cmp byte ptr [rdx],0
  jne .Lblock
  cmp rax,1
  jl .Lblock
  cmp rax,8
  jg .Lblock
  mov qword ptr [rip+max_depth],rax
  mov rax,qword ptr [rip+argv_ptr]
  mov rdi,qword ptr [rax+40]
  lea rsi,[rip+end_ptr]
  mov edx,10
  call strtol@PLT
  mov rdx,qword ptr [rip+end_ptr]
  cmp byte ptr [rdx],0
  jne .Lblock
  cmp rax,1
  jl .Lblock
  mov qword ptr [rip+coll_seed],rax
  call parse_pnv
  test eax,eax
  jz .Lblock
  call read_carriers
  test eax,eax
  jz .Lblock
  # PRECHECK COMPLETE: all pure native maps registered and all sources admitted.
  call vector_kernel
  call verify_vector
  test eax,eax
  jz .Lblock
  call geometry_kernel
  test eax,eax
  jz .Lblock
  call hotel_tree
  test eax,eax
  jz .Lblock
  call collatz_kernel
  test eax,eax
  jz .Lblock
  movsd xmm0,qword ptr [rip+half_d]
  movsd qword ptr [rip+state_d],xmm0
  movsd xmm0,qword ptr [rip+one_d]
  divsd xmm0,qword ptr [rip+ln2_d]
  movsd qword ptr [rip+sigma_d],xmm0
  movsd xmm0,qword ptr [rip+ln2_d]
  divsd xmm0,qword ptr [rip+pi24_d]
  movsd qword ptr [rip+kappa_d],xmm0
  lea rdi,[rip+s_head]
  call puts@PLT
  lea rdi,[rip+s_out_head]
  mov esi,dword ptr [rip+src_bits]
  # all 8 bits, printed 8 not numeric mask
  mov esi,8
  mov edx,MAP_COUNT
  mov ecx,dword ptr [rip+node_count]
  mov r8d,dword ptr [rip+assert_count]
  mov r9d,dword ptr [rip+emit_count]
  xor eax,eax
  call printf@PLT
  lea rdi,[rip+s_out_carrier]
  movsd xmm0,qword ptr [rip+phase_rot36]
  movsd xmm1,qword ptr [rip+phase_rot36+280]
  mov eax,2
  call printf@PLT
  lea rdi,[rip+s_out_ter]
  mov esi,dword ptr [rip+sep_count]
  mov edx,dword ptr [rip+signed_hold_count]
  mov ecx,dword ptr [rip+conn_count]
  xor eax,eax
  call printf@PLT
  lea rdi,[rip+s_out_logic]
  call puts@PLT
  lea rdi,[rip+s_out_sing]
  movsd xmm0,qword ptr [rip+state_d]
  movsd xmm1,qword ptr [rip+sigma_d]
  movsd xmm2,qword ptr [rip+kappa_d]
  movsd xmm3,qword ptr [rip+berry_d]
  movsd xmm4,qword ptr [rip+spin2_d]
  movsd xmm5,qword ptr [rip+spin4_d]
  mov eax,6
  call printf@PLT
  lea rdi,[rip+s_out_bomb]
  mov rsi,qword ptr [rip+bomb_real]
  mov rdx,qword ptr [rip+bomb_imag]
  mov rcx,qword ptr [rip+bomb_norm]
  mov r8,qword ptr [rip+coll_seed]
  mov r9,qword ptr [rip+coll_count]
  xor eax,eax
  call printf@PLT
  lea rdi,[rip+s_out_tzim]
  mov rsi,qword ptr [rip+max_depth]
  xor eax,eax
  call printf@PLT
  mov rbx,qword ptr [rip+guest_room]
  lea rdi,[rip+s_out_room]
  mov rsi,qword ptr [rip+max_depth]
  mov rdx,qword ptr [rip+room_count]
  mov rcx,rbx
  mov r8,qword ptr [rip+guest_k]
  lea r12,[rip+root_re]
  movsd xmm0,qword ptr [r12+rbx*8]
  lea r12,[rip+root_im]
  movsd xmm1,qword ptr [r12+rbx*8]
  lea r12,[rip+root_theta]
  movsd xmm2,qword ptr [r12+rbx*8]
  lea r12,[rip+root_inv]
  movsd xmm3,qword ptr [r12+rbx*8]
  mov eax,4
  call printf@PLT
  lea rdi,[rip+s_out_state]
  call puts@PLT
  lea rdi,[rip+s_out_ok]
  call puts@PLT
  xor eax,eax
  jmp .Lmain_done
.Lusage:
  lea rdi,[rip+s_usage]
  call puts@PLT
  mov eax,2
  jmp .Lmain_done
.Lblock:
  lea rdi,[rip+s_block]
  call puts@PLT
  mov eax,23
.Lmain_done:
  add rsp,16
  pop r12
  pop rbx
  pop rbp
  ret
.section .note.GNU-stack,"",@progbits
