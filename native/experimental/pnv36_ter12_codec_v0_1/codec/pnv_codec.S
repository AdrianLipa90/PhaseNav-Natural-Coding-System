.intel_syntax noprefix
# PNCS experimental PNV36T12 native lossless snapshot codec v0.1
# Copyright 2026 Adrian Lipa. Source-author attribution: Adrian Lipa.
# GAS x86-64 / AVX2; libc file I/O, no Python/C++ interpreter.
# Format: 8 ASCII magic, uint32 LE version 1, uint32 LE total size 320,
#         36 x binary64 LE, 12 x int8 signed TER, FNV-1a32 checksum of first 316 bytes.
# Full, unwrapped 36D phase remains independent from 12 ternary controls.
# 0 trit signifies HOLD(+i,-i) without collapse of the phase36 carrier.
.equ FRAME_BYTES, 320
.equ CONTENT_BYTES, 316
.equ PHASE_N, 36
.equ TER_N, 12
.section .rodata
usage_str: .asciz "Usage: pnv-codec encode phase36.txt trits12.txt state.pnvc | decode state.pnvc"
blocked_str: .asciz "BLOCKED: malformed source, wrong domain, or invalid PNV36T12 frame"
encode_ok: .asciz "PNVC1 ENCODE OK: 36 binary64 lanes, 12 signed TER; HOLD(+i,-i) preserved; snapshot only"
phase_hdr: .asciz "PHASE36 "
trit_hdr: .asciz "TER12 "
read_text: .asciz "r"
read_bin: .asciz "rb"
write_bin: .asciz "wb"
fmt_double_scan: .asciz "%lf"
fmt_int_scan: .asciz "%d"
fmt_extra: .asciz "%95s"
fmt_double_out: .asciz "%.17g%c"
fmt_int_out: .asciz "%d%c"
cmd_encode: .asciz "encode"
cmd_decode: .asciz "decode"
magic: .ascii "PNV36T12"
.section .bss
.align 32
packet: .skip 352
scan_tmp: .skip 16
extra: .skip 96
end_ptr: .skip 8
fp_phase: .skip 8
fp_trit: .skip 8
fp_output: .skip 8
.section .text
.global main
.extern fopen
.extern fclose
.extern fscanf
.extern printf
.extern puts
.extern fwrite
.extern fread
.extern strcmp
.extern strtol

# Computes FNV-1a checksum of byte buffer 0..315. Returns EAX.
.type checksum,@function
checksum:
  lea rdx,[rip+packet]
  mov eax,0x811c9dc5
  xor ecx,ecx
.Lchecksum_next:
  movzx esi,byte ptr [rdx+rcx]
  xor eax,esi
  imul eax,eax,0x01000193
  inc ecx
  cmp ecx,CONTENT_BYTES
  jne .Lchecksum_next
  ret

# Verify packet header, finite binary64 lanes and signed ternary domain.
.type verify_packet,@function
verify_packet:
  push rbx
  lea rbx,[rip+packet]
  mov rax,qword ptr [rip+magic]
  cmp qword ptr [rbx],rax
  jne .Lverify_bad
  cmp dword ptr [rbx+8],1
  jne .Lverify_bad
  cmp dword ptr [rbx+12],FRAME_BYTES
  jne .Lverify_bad
  xor ecx,ecx
.Lverify_phases:
  mov rax,qword ptr [rbx+16+rcx*8]
  mov rdx,0x7ff0000000000000
  and rax,rdx
  cmp rax,rdx
  je .Lverify_bad
  inc ecx
  cmp ecx,PHASE_N
  jne .Lverify_phases
  xor ecx,ecx
.Lverify_trits:
  movsx eax,byte ptr [rbx+304+rcx]
  cmp eax,-1
  jl .Lverify_bad
  cmp eax,1
  jg .Lverify_bad
  inc ecx
  cmp ecx,TER_N
  jne .Lverify_trits
  call checksum
  cmp eax,dword ptr [rip+packet+316]
  jne .Lverify_bad
  mov eax,1
  pop rbx
  ret
.Lverify_bad:
  xor eax,eax
  pop rbx
  ret

# argv: encode phase.txt ter.txt output.pnvc
.type encode,@function
encode:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  push r13
  push r14
  mov r12,rdi
  lea rbx,[rip+packet]
  mov rax,qword ptr [rip+magic]
  mov qword ptr [rbx],rax
  mov dword ptr [rbx+8],1
  mov dword ptr [rbx+12],FRAME_BYTES
  mov rdi,qword ptr [r12+16]
  lea rsi,[rip+read_text]
  call fopen@PLT
  test rax,rax
  jz .Lencode_fail
  mov qword ptr [rip+fp_phase],rax
  xor r13d,r13d
.Lencode_phase_read:
  mov rdi,qword ptr [rip+fp_phase]
  lea rsi,[rip+fmt_double_scan]
  lea rdx,[rip+scan_tmp]
  xor eax,eax
  call fscanf@PLT
  cmp eax,1
  jne .Lencode_fail
  mov rax,qword ptr [rip+scan_tmp]
  mov rdx,0x7ff0000000000000
  and rdx,rax
  mov rcx,0x7ff0000000000000
  cmp rdx,rcx
  je .Lencode_fail
  mov qword ptr [rbx+16+r13*8],rax
  inc r13
  cmp r13,PHASE_N
  jne .Lencode_phase_read
  mov rdi,qword ptr [rip+fp_phase]
  lea rsi,[rip+fmt_extra]
  lea rdx,[rip+extra]
  xor eax,eax
  call fscanf@PLT
  cmp eax,-1
  jne .Lencode_fail
  mov rdi,qword ptr [rip+fp_phase]
  call fclose@PLT
  mov qword ptr [rip+fp_phase],0

  mov rdi,qword ptr [r12+24]
  lea rsi,[rip+read_text]
  call fopen@PLT
  test rax,rax
  jz .Lencode_fail
  mov qword ptr [rip+fp_trit],rax
  xor r13d,r13d
# Parse signed TER text as an entire bounded decimal token, not scanf %d.
# strtol works on signed 64-bit and rejects overflow outside {-1,0,1}.
.Lencode_trit_read:
  mov rdi,qword ptr [rip+fp_trit]
  lea rsi,[rip+fmt_extra]
  lea rdx,[rip+extra]
  xor eax,eax
  call fscanf@PLT
  cmp eax,1
  jne .Lencode_fail
  lea rdi,[rip+extra]
  lea rsi,[rip+end_ptr]
  mov edx,10
  call strtol@PLT
  cmp rax,-1
  jl .Lencode_fail
  cmp rax,1
  jg .Lencode_fail
  mov rdx,qword ptr [rip+end_ptr]
  cmp byte ptr [rdx],0
  jne .Lencode_fail
  mov byte ptr [rbx+304+r13],al
  inc r13
  cmp r13,TER_N
  jne .Lencode_trit_read
  mov rdi,qword ptr [rip+fp_trit]
  lea rsi,[rip+fmt_extra]
  lea rdx,[rip+extra]
  xor eax,eax
  call fscanf@PLT
  cmp eax,-1
  jne .Lencode_fail
  mov rdi,qword ptr [rip+fp_trit]
  call fclose@PLT
  mov qword ptr [rip+fp_trit],0

  # explicit AVX2 lane-copy before sealing the frame: 9 x 4 binary64 = 36.
  lea rdi,[rip+packet+16]
  xor r13d,r13d
.Lencode_avx_copy:
  vmovupd ymm0,ymmword ptr [rdi+r13]
  vmovupd ymmword ptr [rdi+r13],ymm0
  add r13,32
  cmp r13,288
  jne .Lencode_avx_copy
  vzeroupper
  call checksum
  mov dword ptr [rip+packet+316],eax
  mov rdi,qword ptr [r12+32]
  lea rsi,[rip+write_bin]
  call fopen@PLT
  test rax,rax
  jz .Lencode_fail
  mov qword ptr [rip+fp_output],rax
  lea rdi,[rip+packet]
  mov esi,1
  mov edx,FRAME_BYTES
  mov rcx,qword ptr [rip+fp_output]
  call fwrite@PLT
  cmp rax,FRAME_BYTES
  jne .Lencode_fail
  mov rdi,qword ptr [rip+fp_output]
  call fclose@PLT
  mov qword ptr [rip+fp_output],0
  lea rdi,[rip+encode_ok]
  call puts@PLT
  xor eax,eax
  jmp .Lencode_done
.Lencode_fail:
  mov rdi,qword ptr [rip+fp_phase]
  test rdi,rdi
  jz .Lef_skip_phase
  call fclose@PLT
.Lef_skip_phase:
  mov rdi,qword ptr [rip+fp_trit]
  test rdi,rdi
  jz .Lef_skip_ter
  call fclose@PLT
.Lef_skip_ter:
  mov rdi,qword ptr [rip+fp_output]
  test rdi,rdi
  jz .Lef_skip_out
  call fclose@PLT
.Lef_skip_out:
  mov eax,23
.Lencode_done:
  pop r14
  pop r13
  pop r12
  pop rbx
  pop rbp
  ret

# argv: decode input.pnvc ; prints two canonical textual lines
.type decode,@function
decode:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  push r13
  sub rsp,8
  mov r12,rdi
  mov rdi,qword ptr [r12+16]
  lea rsi,[rip+read_bin]
  call fopen@PLT
  test rax,rax
  jz .Ldecode_fail
  mov qword ptr [rip+fp_phase],rax
  lea rdi,[rip+packet]
  mov esi,1
  mov edx,321
  mov rcx,qword ptr [rip+fp_phase]
  call fread@PLT
  cmp rax,FRAME_BYTES
  jne .Ldecode_fail
  mov rdi,qword ptr [rip+fp_phase]
  call fclose@PLT
  mov qword ptr [rip+fp_phase],0
  call verify_packet
  test eax,eax
  jz .Ldecode_fail
  lea rdi,[rip+phase_hdr]
  xor eax,eax
  call printf@PLT
  xor r13d,r13d
  lea rbx,[rip+packet]
.Ldecode_print_phase:
  movsd xmm0,qword ptr [rbx+16+r13*8]
  lea rdi,[rip+fmt_double_out]
  mov esi,32
  cmp r13,35
  jne .Lphase_separator
  mov esi,10
.Lphase_separator:
  mov eax,1
  call printf@PLT
  inc r13
  cmp r13,PHASE_N
  jne .Ldecode_print_phase
  lea rdi,[rip+trit_hdr]
  xor eax,eax
  call printf@PLT
  xor r13d,r13d
.Ldecode_print_ter:
  movsx esi,byte ptr [rbx+304+r13]
  lea rdi,[rip+fmt_int_out]
  mov edx,32
  cmp r13,11
  jne .Lter_separator
  mov edx,10
.Lter_separator:
  xor eax,eax
  call printf@PLT
  inc r13
  cmp r13,TER_N
  jne .Ldecode_print_ter
  xor eax,eax
  jmp .Ldecode_done
.Ldecode_fail:
  mov rdi,qword ptr [rip+fp_phase]
  test rdi,rdi
  jz .Ldecode_no_close
  call fclose@PLT
.Ldecode_no_close:
  mov eax,23
.Ldecode_done:
  add rsp,8
  pop r13
  pop r12
  pop rbx
  pop rbp
  ret

main:
  push rbp
  mov rbp,rsp
  push rbx
  push r12
  mov r12,rsi
  mov ebx,edi
  cmp ebx,5
  je .Lmain_maybe_encode
  cmp ebx,3
  je .Lmain_maybe_decode
  jmp .Lmain_usage
.Lmain_maybe_encode:
  mov rdi,qword ptr [r12+8]
  lea rsi,[rip+cmd_encode]
  call strcmp@PLT
  test eax,eax
  jne .Lmain_usage
  mov rdi,r12
  call encode
  jmp .Lmain_end
.Lmain_maybe_decode:
  mov rdi,qword ptr [r12+8]
  lea rsi,[rip+cmd_decode]
  call strcmp@PLT
  test eax,eax
  jne .Lmain_usage
  mov rdi,r12
  call decode
  jmp .Lmain_end
.Lmain_usage:
  lea rdi,[rip+usage_str]
  call puts@PLT
  mov eax,23
  jmp .Lmain_exit
.Lmain_end:
  test eax,eax
  je .Lmain_exit
  lea rdi,[rip+blocked_str]
  call puts@PLT
  mov eax,23
.Lmain_exit:
  pop r12
  pop rbx
  pop rbp
  ret
.section .note.GNU-stack,"",@progbits
