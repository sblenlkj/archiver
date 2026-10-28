"""Synthetic car fleet demo: no external dependencies or real-world data."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import pi
from typing import Protocol


class FuelType(str, Enum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"


@dataclass(frozen=True)
class Engine:
    model: str
    displacement_l: float
    cylinders: int
    power_kw: float
    torque_nm: float
    fuel: FuelType = FuelType.PETROL

    def horsepower(self) -> float:
        return round(self.power_kw * 1.34102209, 2)

    def specific_power(self) -> float:
        return round(self.power_kw / self.displacement_l, 2)

    def describe(self) -> str:
        return (
            f"{self.model}: {self.cylinders} cylinders, "
            f"{self.displacement_l:.1f} L, {self.horsepower():.1f} hp, "
            f"{self.torque_nm:.0f} Nm"
        )


@dataclass(frozen=True)
class Wheel:
    radius_m: float
    tire_width_mm: int
    pressure_kpa: float

    @property
    def circumference_m(self) -> float:
        return 2 * pi * self.radius_m


@dataclass
class Transmission:
    gears: tuple[float, ...]
    final_drive: float = 3.9
    current_gear: int = 1

    def ratio(self) -> float:
        if not 1 <= self.current_gear <= len(self.gears):
            raise ValueError("Gear is out of range")
        return self.gears[self.current_gear - 1] * self.final_drive

    def shift_up(self) -> None:
        self.current_gear = min(len(self.gears), self.current_gear + 1)

    def shift_down(self) -> None:
        self.current_gear = max(1, self.current_gear - 1)


class Serviceable(Protocol):
    def service(self, odometer_km: int) -> list[str]: ...


@dataclass
class Car:
    vin: str
    make: str
    model: str
    year: int
    engine: Engine
    transmission: Transmission
    wheels: list[Wheel] = field(default_factory=list)
    odometer_km: int = 0
    fuel_liters: float = 45.0
    trip_log: list[dict[str, float]] = field(default_factory=list)

    def drive(self, distance_km: float, consumption_l_per_100km: float) -> None:
        if distance_km < 0 or consumption_l_per_100km < 0:
            raise ValueError("Distance and consumption must not be negative")
        fuel_needed = distance_km * consumption_l_per_100km / 100
        if fuel_needed > self.fuel_liters:
            raise ValueError("Not enough fuel")
        self.fuel_liters -= fuel_needed
        self.odometer_km += round(distance_km)
        self.trip_log.append({"km": distance_km, "fuel": fuel_needed})

    def refuel(self, amount_l: float) -> None:
        if amount_l < 0:
            raise ValueError("Cannot refuel a negative amount")
        self.fuel_liters = min(60.0, self.fuel_liters + amount_l)

    def service(self, odometer_km: int) -> list[str]:
        checks = ["check brakes", "inspect tires", "check fluids"]
        if odometer_km >= 10000:
            checks.append("replace oil and oil filter")
        if odometer_km >= 40000:
            checks.append("inspect transmission")
        return checks

    def summary(self) -> str:
        return (
            f"{self.year} {self.make} {self.model} [{self.vin}] — "
            f"{self.engine.describe()}, odometer {self.odometer_km} km"
        )


@dataclass
class Garage:
    name: str
    cars: list[Car] = field(default_factory=list)

    def add(self, car: Car) -> None:
        if any(existing.vin == car.vin for existing in self.cars):
            raise ValueError("Duplicate VIN")
        self.cars.append(car)

    def find(self, make: str) -> list[Car]:
        return [car for car in self.cars if car.make.casefold() == make.casefold()]

    def total_kilometers(self) -> int:
        return sum(car.odometer_km for car in self.cars)

    def report(self) -> str:
        lines = [f"Garage {self.name}: {len(self.cars)} cars"]
        lines.extend(f"  - {car.summary()}" for car in self.cars)
        lines.append(f"Total odometer: {self.total_kilometers()} km")
        return "\n".join(lines)


def make_demo_garage() -> Garage:
    garage = Garage("Example Garage")
    engines = [
        Engine("Inline Four A", 1.6, 4, 90.0, 155.0),
        Engine("Inline Four B", 2.0, 4, 130.0, 225.0),
        Engine("V6 C", 3.0, 6, 195.0, 320.0),
        Engine("Diesel D", 2.2, 4, 110.0, 370.0, FuelType.DIESEL),
    ]
    for index in range(120):
        engine = engines[index % len(engines)]
        car = Car(
            vin=f"DEMO-CAR-{index:06d}",
            make=("Aurora", "Cobalt", "Meridian")[index % 3],
            model=f"Model-{index % 12}",
            year=2010 + index % 17,
            engine=engine,
            transmission=Transmission((3.8, 2.3, 1.5, 1.1, 0.8)),
            wheels=[Wheel(0.31, 205, 240) for _ in range(4)],
            odometer_km=index * 1729,
        )
        garage.add(car)
    return garage


if __name__ == "__main__":
    print(make_demo_garage().report())
