import json
import os
import atexit
import gc
gc.disable()        

PROPERTY = "pre({r1_valid: true} and {r2_valid: true})"
LOG_FILE_PATH = "/home/baki/ros2_ws_master/oracle_violation_log.jsonl" 

RAD_TO_DEG = 57.29577951308232

violation_logs_buffer = []

INIT_ANGLE = None
DESIRED_ANGLE = 60.0
START_TIME = None

def save_logs_on_exit():
    if not violation_logs_buffer:
        return

    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir: 
        os.makedirs(log_dir, exist_ok=True)
        
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            for raw_time, r1_ok, r2_ok, angle, err_msg in violation_logs_buffer:
                formatted_time = f"{float(raw_time):.3f}" if raw_time is not None else "N/A"
                
                if err_msg: 
                    rule = "Data_Parse_Error"
                    reason = err_msg
                else:
                    rules = []
                    reasons = []
                    if not r1_ok:
                        rules.append("R1_Overshoot_Error")
                        reasons.append(f"Angle limit exceeded. Measured: {angle:.2f}")
                    if not r2_ok:
                        rules.append("R2_Settling_Time_Error")
                        reasons.append(f"Settling time (2s) exceeded. Measured: {angle:.2f}")
                    
                    rule = " & ".join(rules)
                    reason = " | ".join(reasons)
                
                log_file.write(json.dumps({
                    "time": formatted_time,
                    "violated_rule": rule,
                    "reason": reason
                }) + "\n")
        
        print(f"\n[INFO] Toplam {len(violation_logs_buffer)} kural ihlali {LOG_FILE_PATH} dosyasına kaydedildi.")
    except Exception as e:
        print(f"\n[ERROR] Loglar kaydedilirken hata oluştu: {e}")

atexit.register(save_logs_on_exit)

def abstract_message(message):
    global INIT_ANGLE, START_TIME

    pred = {
        'cmd': False,
        'state': False,
        'r1_valid': True,
        'r2_valid': True
    }
    
    topic = message.get('topic')
    current_time = message.get('time')
    
    if current_time is not None:
        pred['time'] = current_time

    if topic == '/model/RotarySingleRod_model/joint/rod_joint/cmd_force':
        pred['cmd'] = True

    elif topic == '/world/RotarySingleRod_world/model/RotarySingleRod_model/joint_state':
        pred['state'] = True
        pos_data = message.get('position')
        
        if pos_data: 
            try:
                if type(pos_data) is str:
                    idx1 = pos_data.find('[') + 1
                    idx2 = pos_data.find(',', idx1)
                    if idx2 == -1: 
                        idx2 = pos_data.find(']', idx1)
                    current_angle_rad = float(pos_data[idx1:idx2])
                else:
                    current_angle_rad = float(pos_data[0])

                current_angle_deg = current_angle_rad * RAD_TO_DEG
                
                if INIT_ANGLE is None:
                    INIT_ANGLE = current_angle_deg
                if START_TIME is None and current_time is not None:
                    START_TIME = current_time

                if INIT_ANGLE < DESIRED_ANGLE:
                    r1_ok = (current_angle_deg < DESIRED_ANGLE + 5.0)
                elif INIT_ANGLE > DESIRED_ANGLE:
                    r1_ok = (current_angle_deg > DESIRED_ANGLE - 5.0)
                else:
                    r1_ok = True
                    
                pred['r1_valid'] = r1_ok

                r2_ok = True
                if START_TIME is not None and (current_time - START_TIME >= 2.0):
                    r2_ok = (DESIRED_ANGLE - 2.0 <= current_angle_deg <= DESIRED_ANGLE + 2.0)
                    pred['r2_valid'] = r2_ok

                if not (r1_ok and r2_ok):
                    violation_logs_buffer.append((current_time, r1_ok, r2_ok, current_angle_deg, None))

            except Exception as e:
                pred['r1_valid'] = False
                pred['r2_valid'] = False
                violation_logs_buffer.append((current_time, False, False, 0.0, f"Position data parsing failed: {e}"))

    return pred






############################################ BU KODDA 4 MS GECİKME VAR ##########################################################
# import json
# import os
# import atexit

# PROPERTY = "pre({r1_valid: true} and {r2_valid: true})"
# LOG_FILE_PATH = "/home/baki/ros2_ws_master/oracle_violation_log.jsonl" 

# RAD_TO_DEG = 57.29577951308232

# violation_logs_buffer = []

# state_vars = {
#     'initial_angle_deg': None,
#     'desired_angle_deg': 60.0,  
#     'start_time': None
# }

# def save_logs_on_exit():
#     if not violation_logs_buffer:
#         return  

#     log_dir = os.path.dirname(LOG_FILE_PATH)
#     if log_dir: 
#         os.makedirs(log_dir, exist_ok=True)
        
#     try:
#         with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
#             for log_entry in violation_logs_buffer:
#                 log_file.write(json.dumps(log_entry) + "\n")
        
#         print(f"\n[INFO] Toplam {len(violation_logs_buffer)} kural ihlali {LOG_FILE_PATH} dosyasına kaydedildi.")
#     except Exception as e:
#         print(f"\n[ERROR] Loglar kaydedilirken hata oluştu: {e}")

# atexit.register(save_logs_on_exit)


# def log_violation(raw_time, rule, reason):
#     formatted_time = f"{float(raw_time):.3f}" if raw_time is not None else "N/A"
    
#     print(f"\n[VIOLATION DETECTED - Time: {formatted_time}]\nRule: {rule}\nReason: {reason}\n")
    
#     violation_logs_buffer.append({
#         "time": formatted_time,
#         "violated_rule": rule,
#         "reason": reason
#     })


# def abstract_message(message):
#     pred = {
#         'cmd': False,
#         'state': False,
#         'r1_valid': True,
#         'r2_valid': True
#     }
    
#     topic = message.get('topic')
#     current_time = message.get('time')
    
#     if current_time is not None:
#         pred['time'] = current_time

#     if topic == '/model/RotarySingleRod_model/joint/rod_joint/cmd_force':
#         pred['cmd'] = True

#     elif topic == '/world/RotarySingleRod_world/model/RotarySingleRod_model/joint_state':
#         pred['state'] = True
#         pos_data = message.get('position')
        
#         if pos_data: 
#             try:
#                 if type(pos_data) is str:
#                     first_val_str = pos_data.split('[', 1)[1].split(',', 1)[0]
#                     current_angle_rad = float(first_val_str)
#                 else:
#                     current_angle_rad = float(pos_data[0])

#                 current_angle_deg = current_angle_rad * RAD_TO_DEG
                
#                 init = state_vars['initial_angle_deg']
#                 des = state_vars['desired_angle_deg']
#                 start_t = state_vars['start_time']
                
#                 if init is None:
#                     init = state_vars['initial_angle_deg'] = current_angle_deg
#                 if start_t is None and current_time is not None:
#                     start_t = state_vars['start_time'] = current_time

#                 if init < des:
#                     r1_ok = (current_angle_deg < des + 5.0)
#                 elif init > des:
#                     r1_ok = (current_angle_deg > des - 5.0)
#                 else:
#                     r1_ok = True
                    
#                 pred['r1_valid'] = r1_ok

#                 r2_ok = True
#                 if start_t is not None and (current_time - start_t >= 2.0):
#                     r2_ok = (des - 2.0 <= current_angle_deg <= des + 2.0)
#                     pred['r2_valid'] = r2_ok

#                 if not (r1_ok and r2_ok):
#                     violated_rules = []
#                     reasons = []
                    
#                     if not r1_ok:
#                         violated_rules.append("R1_Overshoot_Error")
#                         reasons.append(f"Angle limit exceeded. Measured: {current_angle_deg:.2f}")
#                     if not r2_ok:
#                         violated_rules.append("R2_Settling_Time_Error")
#                         reasons.append(f"Settling time (2s) exceeded. Measured: {current_angle_deg:.2f}")
                        
#                     log_violation(current_time, " & ".join(violated_rules), " | ".join(reasons))

#             except Exception as e:
#                 pred['r1_valid'] = False
#                 pred['r2_valid'] = False
#                 log_violation(current_time, "Data_Parse_Error", f"Position data parsing failed: {e}")

#     return pred