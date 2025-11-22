import sys
import math

class Command:
    def __init__(self):
        self.output_destination: Command

    def action(self, input) -> str:
        return self.output_destination.action(input)
    
    def make_command(self) -> str:
        return self.output_destination.make_command()

class Cat(Command):
    def __init__(self, output: Command, flag_path: str):
        self.output_destination = output
        self.path = flag_path

    def action(self, input) -> str:
        return self.output_destination.action(input)
    
    def make_command(self) -> str:
        return "cat " + self.path 

class Echo(Command):
    def __init__(self, output: Command):
        self.output_destination = output

    def action(self, input) -> str:
        return self.output_destination.action(input)

    def make_command(self) -> str:
        return "echo " + self.output_destination.make_command()

class StandardIn(Command):
    def __init__(self, output: Command):
        self.output_destination = output

    def action(self, input) -> str:
        return self.output_destination.action(input)
    
    def input_received(self, input) -> str:
        return self.output_destination.action(input)
    
    def make_command(self) -> str:
        return self.output_destination.make_command()

class StandardOut(Command):
    def __init__(self):
        self.value = None

    def action(self, input) -> str:
        self.value = input
        return input

    def make_command(self) -> str:
        return ""

stdout = StandardOut()
stdin = StandardIn(stdout)

stdin.output_destination = Echo(Cat(stdout, ""))

print("Command to be executed: " + stdin.make_command())