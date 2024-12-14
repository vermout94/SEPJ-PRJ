class Tram:
    def __init__(self, tram_id, capacity, current_passengers=0, current_stop="Depot", max_speed=60):
        """
        Initializes the tram's attributes.
        """
        self.tram_id = tram_id
        self.capacity = capacity
        self.current_passengers = current_passengers
        self.current_stop = current_stop
        self.max_speed = max_speed
        self.is_running = False
        self.current_speed = 0
        self.stops = []

    def add_stop(self, stop_name):
        """
        Adds a stop to the tram's route.
        """
        self.stops.append(stop_name)
        print(f"Stop '{stop_name}' added to the route.")

    def start_tram(self):
        """
        Starts the tram service.
        """
        if not self.is_running:
            self.is_running = True
            print("Tram service started.")
        else:
            print("Tram is already running.")

    def stop_tram(self):
        """
        Stops the tram service.
        """
        if self.is_running:
            self.is_running = False
            self.current_speed = 0
            print("Tram service stopped.")
        else:
            print("Tram is not running.")

    def accelerate(self, increment):
        """
        Accelerates the tram, up to the maximum speed.
        """
        if self.is_running:
            if self.current_speed + increment > self.max_speed:
                self.current_speed = self.max_speed
                print(f"Tram is now at its maximum speed: {self.max_speed} km/h.")
            else:
                self.current_speed += increment
                print(f"Tram accelerated to {self.current_speed} km/h.")
        else:
            print("Cannot accelerate. Tram service is not running.")

    def brake(self, decrement):
        """
        Slows down the tram.
        """
        if self.current_speed > 0:
            self.current_speed = max(0, self.current_speed - decrement)
            print(f"Tram slowed down to {self.current_speed} km/h.")
        else:
            print("Tram is already stationary.")

    def board_passengers(self, count):
        """
        Boards passengers onto the tram, up to its capacity.
        """
        if count <= 0:
            print("Please provide a valid number of passengers.")
        elif self.current_passengers + count > self.capacity:
            print(f"Cannot board all passengers. Only {self.capacity - self.current_passengers} seats available.")
        else:
            self.current_passengers += count
            print(f"{count} passengers boarded. Current passengers: {self.current_passengers}.")

    def disembark_passengers(self, count):
        """
        Allows passengers to leave the tram.
        """
        if count <= 0:
            print("Please provide a valid number of passengers.")
        elif count > self.current_passengers:
            print(f"Cannot disembark {count} passengers. Only {self.current_passengers} are on board.")
        else:
            self.current_passengers -= count
            print(f"{count} passengers disembarked. Current passengers: {self.current_passengers}.")

    def arrive_at_stop(self, stop_name):
        """
        Simulates the tram arriving at a stop.
        """
        if stop_name in self.stops:
            self.current_stop = stop_name
            print(f"Tram has arrived at '{stop_name}'.")
        else:
            print(f"Stop '{stop_name}' is not on the tram's route.")

    def display_status(self):
        """
        Displays the current status of the tram.
        """
        running_status = "Running" if self.is_running else "Not Running"
        print("Tram Status:")
        print(f"  Tram ID: {self.tram_id}")
        print(f"  Current Stop: {self.current_stop}")
        print(f"  Current Passengers: {self.current_passengers}/{self.capacity}")
        print(f"  Current Speed: {self.current_speed} km/h")
        print(f"  Maximum Speed: {self.max_speed} km/h")
        print(f"  Status: {running_status}")
        print(f"  Route Stops: {', '.join(self.stops) if self.stops else 'No stops added.'}")

# Example usage:
if __name__ == "__main__":
    tram = Tram(tram_id="T100", capacity=100, max_speed=80)
    tram.add_stop("Central Station")
    tram.add_stop("City Square")
    tram.add_stop("University")
    tram.display_status()
    tram.start_tram()
    tram.accelerate(30)
    tram.arrive_at_stop("Central Station")
    tram.board_passengers(50)
    tram.accelerate(20)
    tram.arrive_at_stop("City Square")
    tram.disembark_passengers(20)
    tram.stop_tram()
    tram.display_status()
