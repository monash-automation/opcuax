from pydantic import BaseModel, NonNegativeFloat


class PrinterHead(BaseModel):
    x: float
    y: float
    z: float


class PrinterJob(BaseModel):
    file: str = "N/A"
    progress: NonNegativeFloat
    time_left: NonNegativeFloat
    time_left_approx: NonNegativeFloat
    time_used: NonNegativeFloat


class Temperature(BaseModel):
    actual: NonNegativeFloat
    target: NonNegativeFloat


class Printer(BaseModel):
    state: str
    nozzle: Temperature
    bed: Temperature

    head: PrinterHead
    job: PrinterJob
