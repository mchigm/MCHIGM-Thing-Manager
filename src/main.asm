; MCHIGM Thing Manager - Main Entry Point
; Linux x86-64 Assembly Implementation
; Author: MCHIGM Team
; Description: CLI application for managing time planners and timetables

section .data
    ; Menu strings
    welcome_msg db "=== MCHIGM Thing Manager ===", 10, 0
    welcome_len equ $ - welcome_msg
    
    menu_msg db 10, "Main Menu:", 10
             db "1. Create Time Planner", 10
             db "2. Create Timetable", 10
             db "3. List All Items", 10
             db "4. Exit", 10
             db "Select option: ", 0
    menu_len equ $ - menu_msg
    
    ; Time Planner prompts
    planner_prompt db 10, "Enter time planner name (max 50 chars): ", 0
    planner_prompt_len equ $ - planner_prompt
    
    planner_desc_prompt db "Enter description (max 100 chars): ", 0
    planner_desc_prompt_len equ $ - planner_desc_prompt
    
    planner_time_prompt db "Enter time (HH:MM format): ", 0
    planner_time_prompt_len equ $ - planner_time_prompt
    
    ; Timetable prompts
    timetable_prompt db 10, "Enter timetable name (max 50 chars): ", 0
    timetable_prompt_len equ $ - timetable_prompt
    
    timetable_day_prompt db "Enter day (Monday-Sunday): ", 0
    timetable_day_prompt_len equ $ - timetable_day_prompt
    
    timetable_time_prompt db "Enter time slot (e.g., 09:00-10:00): ", 0
    timetable_time_prompt_len equ $ - timetable_time_prompt
    
    ; Success messages
    planner_created db 10, "Time planner created successfully!", 10, 0
    planner_created_len equ $ - planner_created
    
    timetable_created db 10, "Timetable created successfully!", 10, 0
    timetable_created_len equ $ - timetable_created
    
    ; List header
    list_header db 10, "=== All Items ===", 10, 0
    list_header_len equ $ - list_header
    
    planner_label db "Time Planner: ", 0
    planner_label_len equ $ - planner_label
    
    timetable_label db "Timetable: ", 0
    timetable_label_len equ $ - timetable_label
    
    ; Error messages
    invalid_option db "Invalid option. Please try again.", 10, 0
    invalid_option_len equ $ - invalid_option
    
    exit_msg db "Thank you for using MCHIGM Thing Manager!", 10, 0
    exit_msg_len equ $ - exit_msg
    
    newline db 10
    
    ; File paths for storing data
    planners_file db "data/planners.txt", 0
    timetables_file db "data/timetables.txt", 0

section .bss
    input_buffer resb 256      ; Buffer for user input
    name_buffer resb 51        ; Buffer for name
    desc_buffer resb 101       ; Buffer for description
    time_buffer resb 11        ; Buffer for time
    day_buffer resb 16         ; Buffer for day
    timeslot_buffer resb 21    ; Buffer for time slot
    choice resb 2              ; User's menu choice
    file_buffer resb 4096      ; Buffer for reading files

section .text
    global _start

_start:
    ; Display welcome message
    call display_welcome
    
main_loop:
    ; Display menu
    call display_menu
    
    ; Read user choice
    call read_choice
    
    ; Process choice
    cmp byte [choice], '1'
    je create_time_planner
    
    cmp byte [choice], '2'
    je create_timetable
    
    cmp byte [choice], '3'
    je list_items
    
    cmp byte [choice], '4'
    je exit_program
    
    ; Invalid choice
    call display_invalid
    jmp main_loop

display_welcome:
    mov rax, 1                 ; sys_write
    mov rdi, 1                 ; stdout
    mov rsi, welcome_msg
    mov rdx, welcome_len
    syscall
    ret

display_menu:
    mov rax, 1
    mov rdi, 1
    mov rsi, menu_msg
    mov rdx, menu_len
    syscall
    ret

read_choice:
    ; Read user input
    mov rax, 0                 ; sys_read
    mov rdi, 0                 ; stdin
    mov rsi, choice
    mov rdx, 2
    syscall
    ret

display_invalid:
    mov rax, 1
    mov rdi, 1
    mov rsi, invalid_option
    mov rdx, invalid_option_len
    syscall
    ret

create_time_planner:
    ; Prompt for planner name
    mov rax, 1
    mov rdi, 1
    mov rsi, planner_prompt
    mov rdx, planner_prompt_len
    syscall
    
    ; Read name
    mov rax, 0
    mov rdi, 0
    mov rsi, name_buffer
    mov rdx, 51
    syscall
    
    ; Prompt for description
    mov rax, 1
    mov rdi, 1
    mov rsi, planner_desc_prompt
    mov rdx, planner_desc_prompt_len
    syscall
    
    ; Read description
    mov rax, 0
    mov rdi, 0
    mov rsi, desc_buffer
    mov rdx, 101
    syscall
    
    ; Prompt for time
    mov rax, 1
    mov rdi, 1
    mov rsi, planner_time_prompt
    mov rdx, planner_time_prompt_len
    syscall
    
    ; Read time
    mov rax, 0
    mov rdi, 0
    mov rsi, time_buffer
    mov rdx, 11
    syscall
    
    ; Save to file
    call save_planner
    
    ; Display success message
    mov rax, 1
    mov rdi, 1
    mov rsi, planner_created
    mov rdx, planner_created_len
    syscall
    
    jmp main_loop

create_timetable:
    ; Prompt for timetable name
    mov rax, 1
    mov rdi, 1
    mov rsi, timetable_prompt
    mov rdx, timetable_prompt_len
    syscall
    
    ; Read name
    mov rax, 0
    mov rdi, 0
    mov rsi, name_buffer
    mov rdx, 51
    syscall
    
    ; Prompt for day
    mov rax, 1
    mov rdi, 1
    mov rsi, timetable_day_prompt
    mov rdx, timetable_day_prompt_len
    syscall
    
    ; Read day
    mov rax, 0
    mov rdi, 0
    mov rsi, day_buffer
    mov rdx, 16
    syscall
    
    ; Prompt for time slot
    mov rax, 1
    mov rdi, 1
    mov rsi, timetable_time_prompt
    mov rdx, timetable_time_prompt_len
    syscall
    
    ; Read time slot
    mov rax, 0
    mov rdi, 0
    mov rsi, timeslot_buffer
    mov rdx, 21
    syscall
    
    ; Save to file
    call save_timetable
    
    ; Display success message
    mov rax, 1
    mov rdi, 1
    mov rsi, timetable_created
    mov rdx, timetable_created_len
    syscall
    
    jmp main_loop

save_planner:
    ; Open file for appending (create if doesn't exist)
    mov rax, 2                 ; sys_open
    mov rdi, planners_file
    mov rsi, 0x441             ; O_WRONLY | O_CREAT | O_APPEND
    mov rdx, 0644o             ; File permissions
    syscall
    
    ; Check if open was successful
    cmp rax, 0
    jl save_planner_end
    
    mov r12, rax               ; Save file descriptor
    
    ; Write "Time Planner: " label
    mov rax, 1                 ; sys_write
    mov rdi, r12
    mov rsi, planner_label
    mov rdx, planner_label_len
    syscall
    
    ; Write name
    mov rax, 1
    mov rdi, r12
    mov rsi, name_buffer
    mov rdx, 51
    syscall
    
    ; Write description
    mov rax, 1
    mov rdi, r12
    mov rsi, desc_buffer
    mov rdx, 101
    syscall
    
    ; Write time
    mov rax, 1
    mov rdi, r12
    mov rsi, time_buffer
    mov rdx, 11
    syscall
    
    ; Write newline
    mov rax, 1
    mov rdi, r12
    mov rsi, newline
    mov rdx, 1
    syscall
    
    ; Close file
    mov rax, 3                 ; sys_close
    mov rdi, r12
    syscall
    
save_planner_end:
    ret

save_timetable:
    ; Open file for appending (create if doesn't exist)
    mov rax, 2                 ; sys_open
    mov rdi, timetables_file
    mov rsi, 0x441             ; O_WRONLY | O_CREAT | O_APPEND
    mov rdx, 0644o             ; File permissions
    syscall
    
    ; Check if open was successful
    cmp rax, 0
    jl save_timetable_end
    
    mov r12, rax               ; Save file descriptor
    
    ; Write "Timetable: " label
    mov rax, 1                 ; sys_write
    mov rdi, r12
    mov rsi, timetable_label
    mov rdx, timetable_label_len
    syscall
    
    ; Write name
    mov rax, 1
    mov rdi, r12
    mov rsi, name_buffer
    mov rdx, 51
    syscall
    
    ; Write day
    mov rax, 1
    mov rdi, r12
    mov rsi, day_buffer
    mov rdx, 16
    syscall
    
    ; Write time slot
    mov rax, 1
    mov rdi, r12
    mov rsi, timeslot_buffer
    mov rdx, 21
    syscall
    
    ; Write newline
    mov rax, 1
    mov rdi, r12
    mov rsi, newline
    mov rdx, 1
    syscall
    
    ; Close file
    mov rax, 3                 ; sys_close
    mov rdi, r12
    syscall
    
save_timetable_end:
    ret

list_items:
    ; Display header
    mov rax, 1
    mov rdi, 1
    mov rsi, list_header
    mov rdx, list_header_len
    syscall
    
    ; Try to display planners
    call display_file_contents
    
    jmp main_loop

display_file_contents:
    ; Try to open planners file
    mov rax, 2                 ; sys_open
    mov rdi, planners_file
    mov rsi, 0                 ; O_RDONLY
    syscall
    
    cmp rax, 0
    jl try_timetables          ; If file doesn't exist, skip
    
    mov r12, rax               ; Save file descriptor
    
    ; Read file contents
    mov rax, 0                 ; sys_read
    mov rdi, r12
    mov rsi, file_buffer
    mov rdx, 4096
    syscall
    
    mov r13, rax               ; Save bytes read
    
    ; Close file
    mov rax, 3
    mov rdi, r12
    syscall
    
    ; Display contents if any
    cmp r13, 0
    jle try_timetables
    
    mov rax, 1
    mov rdi, 1
    mov rsi, file_buffer
    mov rdx, r13
    syscall
    
try_timetables:
    ; Try to open timetables file
    mov rax, 2                 ; sys_open
    mov rdi, timetables_file
    mov rsi, 0                 ; O_RDONLY
    syscall
    
    cmp rax, 0
    jl display_file_end        ; If file doesn't exist, skip
    
    mov r12, rax               ; Save file descriptor
    
    ; Read file contents
    mov rax, 0                 ; sys_read
    mov rdi, r12
    mov rsi, file_buffer
    mov rdx, 4096
    syscall
    
    mov r13, rax               ; Save bytes read
    
    ; Close file
    mov rax, 3
    mov rdi, r12
    syscall
    
    ; Display contents if any
    cmp r13, 0
    jle display_file_end
    
    mov rax, 1
    mov rdi, 1
    mov rsi, file_buffer
    mov rdx, r13
    syscall
    
display_file_end:
    ret

exit_program:
    ; Display exit message
    mov rax, 1
    mov rdi, 1
    mov rsi, exit_msg
    mov rdx, exit_msg_len
    syscall
    
    ; Exit
    mov rax, 60                ; sys_exit
    xor rdi, rdi               ; Exit code 0
    syscall
