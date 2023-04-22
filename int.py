from intbase import InterpreterBase, ErrorType
from bparser import BParser
from enum import Enum

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None):
        super().__init__(console_output, inp)
        self.classes = {}

    def run(self, program):
        result, parsed_program = BParser.parse(program)
        if result == False:
            return  # error

        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.__find_definition_for_class("main")
        obj = class_def.instantiate_object()
        obj.call_method("main", [])

    def __discover_all_classes_and_track_them(self, parsed_program):
        for class_def in parsed_program:
            class_name = class_def[1]
            self.classes[class_name] = ClassDefinition(class_def)

    def __find_definition_for_class(self, class_name):
        return self.classes[class_name]


class ClassDefinition:
    def __init__(self, class_name):
        self.class_name = class_name
        self.fields = {}  # Dictionary to store fields
        self.methods = {}  # Dictionary to store methods

    def add_field(self, field_name, field):
        self.fields[field_name] = field

    def add_method(self, method_name, method):
        self.methods[method_name] = method

    def instantiate_object(self):
        print(self.fields)
        print(self.methods)
        obj = ObjectDefinition(self.class_name)
        for field_name, field in self.fields.items():
            obj.add_field(field_name, field)
        for method_name, method in self.methods.items():
            obj.add_method(method_name, method)
        return obj



class ObjectDefinition:
    def __init__(self, class_name):
        self.class_name = class_name
        self.fields = {}  # Dictionary to store fields
        self.methods = {}  # Dictionary to store methods

    def add_field(self, field_name, field):
        self.fields[field_name] = field

    def add_method(self, method_name, method):
        self.methods[method_name] = method

    def call_method(self, method_name, parameters):
        if method_name in self.methods:
            method = self.methods[method_name]
            result = method.execute(self, parameters)
            return result
        else:
            raise KeyError(f"Method '{method_name}' not found in the object.")

    def set_field_value(self, field_name, value):
        if field_name in self.fields:
            self.fields[field_name] = value
        else:
            raise KeyError(f"Field '{field_name}' not found in the object.")

    def get_field_value(self, field_name):
        if field_name in self.fields:
            return self.fields[field_name]
        else:
            raise KeyError(f"Field '{field_name}' not found in the object.")


    def __run_statement(self, statement):
        statement_type = statement[0]

        if statement_type == InterpreterBase.PRINT_DEF:
            return self.__execute_print_statement(statement)
        elif statement_type == InterpreterBase.INPUT_STRING_DEF:
            return self.__execute_input_string_statement(statement)
        elif statement_type == InterpreterBase.INPUT_INT_DEF:
            return self.__execute_input_int_statement(statement)
        elif statement_type == InterpreterBase.CALL_DEF:
            return self.__execute_call_statement(statement)
        # Add more logic for other statement types

    def __execute_print_statement(self, statement):
        value = statement[1]
        self.output(value)
        return None

    def __execute_input_string_statement(self, statement):
        field_name = statement[1]
        input_value = self.get_input()
        self.fields[field_name] = input_value
        return None

    def __execute_input_int_statement(self, statement):
        field_name = statement[1]
        input_value = int(self.get_input())
        self.fields[field_name] = input_value
        return None

    def __execute_call_statement(self, statement):
        method_name = statement[1]
        parameters = statement[2:]
        return self.call_method(method_name, parameters)

    # Implement additional methods for handling different statement types

def main():
    source_code = ['(class main',
                    ' (field name 0)',
                    ' (method main ()',
                    '  (print "hello world!")',
                    ' ) # end of method',
                    ') # end of class',
                    '(class person',
                    ')',
                    ]
    
    test_source_code = """
    (class person
         (field name "")
         (field age 0)
         (method init (n a)
            (begin
              (set name n)
              (set age a)
            )
         )
         (method talk (to_whom)
            (print name " says hello to " to_whom)
         )
      )

(class main
 (field p null)
 (method tell_joke (to_whom)
    (print "Hey " to_whom ", knock knock!")
 )
 (method main ()
   (begin
      (call me tell_joke "Matt") # call tell_joke in current object
      (set p (new person))  # allocate a new person obj, point p at it
      (call p init "Siddarth" 25) # call init in object pointed to by p
      (call p talk "Paul")       # call talk in object pointed to by p
   )
 )
)
""".split('\n')
    interpreter = Interpreter()
    interpreter.run(source_code)

if __name__ == '__main__':
    main()