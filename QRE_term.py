import serial

from crccheck.crc import Crc8

from serial.tools.list_ports import comports
from serial.tools import hexlify_codec
from Tkinter import *
import ttk

# -- Custom commands, not listed in the original protocol
#
# CUPS:
#
# 0xC1 0x10 0x7F 0x2D 0xC0 Go to the next task
# 0xC1 0x10 0x7E 0x2A 0xC0 Restart current task
# 0xC1 0x10 0x7D 0x23 0xC0 Test 7 segement display
# 0xC1 0x10 0x7C 0x24 0xC0 Ask what task is now active
# 0xC1 0x10 0x7A 0x36 0xC0 Ask what is threshold value in Silence Detection
#
# HORSES:
#
# 0xC1 0x0B 0x78 <speed> 0x01 0xE1 0xC0				Motor 1 forward at <speed>
# 0xC1 0x0B 0x78 <speed> 0x02 0xE8 0xC0				Motor 1 reverse at <speed>
# 0xC1 0x0B 0x78 <speed> 0x03 0xEF 0xC0 			Motor 2 forward at <speed>
# 0xC1 0x0B 0x78 <speed> 0x04 0xFA 0xC0 			Motor 2 reverse at <speed>
#
# 108 < speed > 2550  Speed selection formula: 108+10*incoming_packet.motor_speed

TST =       "\x01"    # 0xC1 <_dev> 0x01 <_CRC> 0xC0 Tests
WS =        "\x02"    # 0xC1 <_dev> 0x02 <_CRC> 0xC0 Work Start
SR =        "\x03"    # 0xC1 <_dev> 0x03 <_CRC> 0xC0 Stauts request
IDLE=       "\x04"    # 0xC1 <_dec> 0x04 <_CRC> 0xC0 Idle

SYS_RESET = "\x79"    # 0xC1 <> 0x79 0xFF <_CRC> Perform system reset

C_NT =      "\x7F"
C_RCT =     "\x7E"
C_T7SD =    "\x7D"
C_WTIS =    "\x7C"
C_WITVSD =  "\x7A"

H_TVS =     "\x78"

H_M1F =     "\x01"
H_M1R =     "\x02"
H_M2F =     "\x03"
H_M2R =     "\x04"

CUPS = "\x10"
HORSES = "\x0B"

START_B = "\xC1"
STOP_B  = "\xC0"

CRC_POLYNOM = "\x07"

default_button_width = 16
custom_button_width = 22

active_device = None

ser = serial.Serial(None, 19200, bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0)

root = Tk()
root.title("QRE 485 Control terminal")
root.geometry("380x320")


ports = []

app = Frame(root)
app.grid()

menubar = Menu(root)
portMenu = Menu(menubar, tearoff = 0)
devMenu = Menu(menubar, tearoff = 0)

default_commands_lf = LabelFrame(root, text = "Default commands",padx=12,pady=20,labelanchor=N)
default_commands_lf.grid(row=0)

cups_commands_lf = LabelFrame(root, text = "Cups commands",padx=12,pady=25,labelanchor=N)


custom_button = Button(cups_commands_lf, text = "Next Task", command = lambda: send_cmd(assemble_packet(C_NT, CUPS)), width = custom_button_width).grid()
custom_button = Button(cups_commands_lf, text = "Restart Task", command = lambda: send_cmd(assemble_packet(C_RCT, CUPS)), width = custom_button_width).grid()
custom_button = Button(cups_commands_lf, text = "Test 7-seg display", command = lambda: send_cmd(assemble_packet(C_T7SD, CUPS)), width = custom_button_width).grid()
custom_button = Button(cups_commands_lf, text = "What task is active?", command = lambda: send_cmd(assemble_packet(C_WTIS, CUPS)), width = custom_button_width).grid()
custom_button = Button(cups_commands_lf, text = "Silence detection threshold?", command = lambda: send_cmd(assemble_packet(C_WITVSD, CUPS)), width = custom_button_width).grid()

horses_commands_lf = LabelFrame(root, text = "Horses commands",padx=12,pady=16,labelanchor=N)
            
motor1_lf = LabelFrame(horses_commands_lf, text = "Motor 1")
motor1_lf.grid(column=2, row=1)

_motor_selection = IntVar()
_motor_selection.set(1)
_motor_speed = IntVar()

custom_button = Radiobutton(motor1_lf, text = "Forward", value=1, variable=_motor_selection).grid()
custom_button = Radiobutton(motor1_lf, text = "Reverse", value=2, variable=_motor_selection).grid()


motor2_lf = LabelFrame(horses_commands_lf, text = "Motor 2")
motor2_lf.grid(column=3, row=1)

custom_button = Radiobutton(motor2_lf, text = "Forward", value=3, variable=_motor_selection).grid()
custom_button = Radiobutton(motor2_lf, text = "Reverse", value=4, variable=_motor_selection).grid()

motor_spin_button = Button(horses_commands_lf, text = "Spin!", command = lambda: send_cmd(assemble_packet(H_TVS, HORSES, convert_motor_speed(), chr(_motor_selection.get()) ))).grid(row=4,columnspan=4,sticky=W+E)

motor_speed_slider = Scale(horses_commands_lf, orient=HORIZONTAL, to=255, label="Speed:", variable=_motor_speed).grid(row=3,columnspan=4,sticky=W+E)

port_last_used=None

def convert_motor_speed():
    return(chr(255-_motor_speed.get()))  

def send_cmd(_cmd):
    ser.write(_cmd)

def calc_crc8(_packet):
    data = bytearray(_packet)
    crc = Crc8.calc(data)
    crchex = hex(crc)
    return chr(crc)
                 
def assemble_packet(_cmd, _dev, _speed = None, _motor_sel = None):
    if(_speed == None and _motor_sel == None): outgoing_packet = START_B + _dev + _cmd + calc_crc8(_dev + _cmd) + STOP_B
    elif(_speed != None and _motor_sel != None): outgoing_packet = START_B + _dev + _cmd + _speed + _motor_sel + calc_crc8(_dev + _cmd) + STOP_B
    return outgoing_packet

def select_port(_port):
    print(str(_device_selection.get()))
    print(_port)
    print(port_last_used)

    global port_last_used
    
    if(ser.is_open==True):
        if(_port == port_last_used):
            ser.close()
            ser.port = None
            _port_selection.set(0)
            print("Port",_port," closed!")
            return
        if(_port != port_last_used):
            ser.close()
            ser.port=_port
            print("Port",_port,"Opened instead of ", port_last_used)
            port_last_used=_port
            ser.open()
            return
    if(ser.is_open==False):
        ser.port=_port
        ser.open()
        port_last_used = _port
        print("Port",_port," is opened!")
        return
    

    
    #label = Label(app, text = "You've selected port: {}".format(__port))


def select_device(_dev):
    if(_dev == CUPS):
        horses_commands_lf.grid_forget()
        cups_commands_lf.grid(column=1, row=0,sticky=N)
    if(_dev == HORSES):
        cups_commands_lf.grid_forget()  
        horses_commands_lf.grid(column=1, row=0,sticky=N)
              

_port_selection = IntVar()

for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
    ports.append(port)
    portMenu.add_checkbutton(label=port, onvalue=n, offvalue=n, variable=_port_selection, command = lambda port=port: select_port(port))

_device_selection = IntVar()

menubar.add_cascade(label="PORT", menu=portMenu)
menubar.add_cascade(label="Device", menu=devMenu)

devMenu.add_checkbutton(label="Cups", onvalue=1, offvalue=1, variable=_device_selection, command = lambda: select_device(CUPS))
devMenu.add_checkbutton(label="Horses", onvalue=2, offvalue=2, variable=_device_selection, command = lambda: select_device(HORSES))


root.config(menu=menubar)


default_button = Button(default_commands_lf, text = "Test",           command = lambda: send_cmd(assemble_packet(TST, CUPS)), width = default_button_width).grid()
default_button = Button(default_commands_lf, text = "Work Start",     command = lambda: send_cmd(assemble_packet(WS, CUPS)), width = default_button_width).grid()
default_button = Button(default_commands_lf, text = "Status Request", command = lambda: send_cmd(assemble_packet(SR, CUPS)), width = default_button_width).grid()
default_button = Button(default_commands_lf, text = "Idle",           command = lambda: send_cmd(assemble_packet(IDLE, CUPS)), width = default_button_width).grid()
default_button = Button(default_commands_lf, text = "System Reset",   command = lambda: send_cmd(assemble_packet(SYS_RESET, CUPS)), width = default_button_width).grid(pady=5)

default_commands_lf.grid()




root.mainloop()











