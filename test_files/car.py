class Car:
    def __init__(self, make, model, year, color, fuel_capacity, fuel_level=0):
        """
        Initializes the car's attributes.
        """
        self.make = make
        self.model = model
        self.year = year
        self.color = color
        self.fuel_capacity = fuel_capacity
        self.fuel_level = fuel_level
        self.is_engine_on = False
        self.current_speed = 0

    def start_engine(self):
        """
        Starts the car's engine.
        """
        if not self.is_engine_on:
            self.is_engine_on = True
            print("Engine started.")
        else:
            print("Engine is already running.")

    def stop_engine(self):
        """
        Stops the car's engine.
        """
        if self.is_engine_on:
            self.is_engine_on = False
            print("Engine stopped.")
        else:
            print("Engine is already off.")

    def accelerate(self, increment):
        """
        Accelerates the car by a specified increment.
        """
        if self.is_engine_on:
            self.current_speed += increment
            print(f"Accelerated to {self.current_speed} km/h.")
        else:
            print("Cannot accelerate. The engine is off.")

    def brake(self, decrement):
        """
        Applies the brakes to reduce the car's speed.
        """
        if self.current_speed > 0:
            self.current_speed = max(0, self.current_speed - decrement)
            print(f"Slowed down to {self.current_speed} km/h.")
        else:
            print("The car is already stationary.")

    def refuel(self, amount):
        """
        Refuels the car by a specified amount.
        """
        if amount <= 0:
            print("Please provide a valid amount of fuel to refuel.")
        else:
            if self.fuel_level + amount > self.fuel_capacity:
                print(f"Overfilled! You can only add {self.fuel_capacity - self.fuel_level} liters.")
            else:
                self.fuel_level += amount
                print(f"Refueled {amount} liters. Current fuel level: {self.fuel_level} liters.")

    def honk(self):
        """
        Honks the horn.
        """
        print("Beep beep!")

    def repaint(self, new_color):
        """
        Changes the car's color.
        """
        print(f"Repainting the car from {self.color} to {new_color}.")
        self.color = new_color
        print(f"The car is now {self.color}.")

    def display_status(self):
        """
        Displays the current status of the car.
        """
        engine_status = "On" if self.is_engine_on else "Off"
        print("Car Status:")
        print(f"  Make: {self.make}")
        print(f"  Model: {self.model}")
        print(f"  Year: {self.year}")
        print(f"  Color: {self.color}")
        print(f"  Fuel Capacity: {self.fuel_capacity} liters")
        print(f"  Fuel Level: {self.fuel_level} liters")
        print(f"  Engine: {engine_status}")
        print(f"  Current Speed: {self.current_speed} km/h")

# Example usage:
if __name__ == "__main__":
    my_car = Car("Toyota", "Corolla", 2020, "Red", 50)
    my_car.display_status()
    my_car.start_engine()
    my_car.accelerate(20)
    my_car.brake(10)
    my_car.honk()
    my_car.refuel(30)
    my_car.repaint("Blue")
    my_car.stop_engine()
    my_car.display_status()


