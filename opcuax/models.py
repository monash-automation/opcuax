from opcuax.client import OpcuaFloatVar, OpcuaObject, OpcuaStrVar


class PrinterHead(OpcuaObject):
    x = OpcuaFloatVar(name="X")
    y = OpcuaFloatVar(name="Y")
    z = OpcuaFloatVar(name="Z")


class PrinterJob(OpcuaObject):
    file = OpcuaStrVar(name="File")
    progress = OpcuaFloatVar(name="Progress")
    time_left = OpcuaFloatVar(name="TimeLeft")
    time_left_approx = OpcuaFloatVar(name="TimeLeftApprox")
    time_used = OpcuaFloatVar(name="TimeUsed")


class Printer(OpcuaObject):
    state = OpcuaStrVar(name="State")
    noz_act_temp = OpcuaFloatVar(name="NozzleActualTemperature")
    bed_act_temp = OpcuaFloatVar(name="BedActualTemperature")
    noz_tar_temp = OpcuaFloatVar(name="NozzleTargetTemperature")
    bed_tar_temp = OpcuaFloatVar(name="BedTargetTemperature")

    head = PrinterHead(name="Head")
    job = PrinterJob(name="LatestJob")
