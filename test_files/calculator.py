class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, amount):
        self.value += amount

    def subtract(self, amount):
        self.value -= amount

    def display(self):
        print(f"Current value: {self.value}")

calc = Calculator()
calc.add(10)
calc.subtract(3)
calc.display()
