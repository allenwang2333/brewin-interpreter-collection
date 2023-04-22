from intbase import InterpreterBase, ErrorType
from bparser import BParser
from enum import Enum

class Interpreter(InterpreterBase):
    """Interpreter Class"""
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.all_classes = {} # dict: {key=class_name, value = class description}

    def run(self, program_source):
        # first parse the program
        result, parsed_program = BParser.parse(program_source)
        if result == False:
            self.error(ErrorType.SYNTAX_ERROR, "invalid input")
        print(parsed_program) # ! delete this before submission

        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.__find_definition_for_class(self.MAIN_CLASS_DEF)
        obj = class_def.instantiate_object() 
        obj.run_method(InterpreterBase.MAIN_FUNC_DEF)
    
    def __discover_all_classes_and_track_them(self, parsed_program):
        # find all classes and put them is all_classes
        self.class_manager = ClassManager(parsed_program, self.CLASS_DEF)
        for class_def in parsed_program:
            if class_def[1] not in self.all_classes and class_def[0] == self.CLASS_DEF:
                self.all_classes[class_def[1]] = ClassDefinition(class_def[1], class_def[2:], self)
            else:
                self.error(ErrorType.NAME_ERROR, f"duplicate class name {class_def[1]} {class_def[1].line_num}")
            # ! check if the program has at least one class
            
    def __find_definition_for_class(self, class_name):
        if class_name in self.all_classes:
            return self.all_classes[class_name]
        else:
            self.error(ErrorType.NAME_ERROR, f"class {class_name} can't be found")

class ClassManager:
    """Keep Track of class location"""
    def __init__(self, parsed_program, class_definition):
        self.class_location = {}
        self.__add_all_classes(parsed_program, class_definition)
    
    def __add_all_classes(self, parsed_program, class_definition):
        for i in range(len(parsed_program)):
            if parsed_program[i][0] == class_definition:
                self.class_location[parsed_program[i][1]] = i
    
    def get_class_location(self, class_name):
        if class_name not in self.class_location.keys():
            return ErrorType.NAME_ERROR
        return self.class_location[class_name]
        

class ClassDefinition:
    def __init__(self, name, class_definition, interpreter):
        self.my_name = name
        self.my_class_definition = class_definition
        self.my_methods = [] # a list of description of methods
        self.my_fields = [] # ! can be optimized by hash table
        self.interpreter = interpreter
        for item in class_definition: 
            if item[0] == 'field' and item not in self.my_fields:
                self.my_fields.append(item)
            elif item[0] == 'method' and item not in self.my_methods:
                self.my_methods.append(item)
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, "duplicate names")
    
    # uses the definition of a class to create and return an instance of it
    def instantiate_object(self): 
        obj = ObjectDefinition(self.interpreter)
        for method in self.my_methods:
            obj.add_method(method)
            
        for field in self.my_fields:
            obj.add_field(field)
            
        return obj


class ObjectDefinition:
    def __init__(self, interpreter):
        self.obj_methods = {}
        self.interpreter = interpreter
        self.obj_variables = {}

    def add_method(self, method):
        self.obj_methods[method[1]] = Method(method[1], method[2], method[3])

    def add_field(self, field):
        self.obj_variables[field[1]] = Value(field[2])

   # Interpret the specified method using the provided parameters    
    def run_method(self, method_name, parameters=[]):
        method = self.__find_method(method_name)
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement)
        return result
    
    def __find_method(self, method_name):
        if method_name in self.obj_methods:
            return self.obj_methods[method_name]
        else:
            self.interpreter.error(ErrorType.NAME_ERROR, "method undefined")

  # runs/interprets the passed-in statement until completion and 
  # gets the result, if any
    def __run_statement(self, statement):
        if is_a_print_statement(statement):
            result = self.__execute_print_statement(statement)
        elif is_an_input_statement(statement):
            result = self.__execute_input_statement(statement)
        elif is_a_set_statement(statement):
            result = self.__execute_set_statement(statement)
        elif is_a_call_statement(statement):
            result = self.__execute_call_statement(statement)
        elif is_a_while_statement(statement):
            result = self.__execute_while_statement(statement)
        elif is_an_if_statement(statement):
            result = self.__execute_if_statement(statement)
        elif is_a_return_statement(statement):
            result = self.__execute_return_statement(statement)
        elif is_a_begin_statement(statement):
            result = self.__execute_all_sub_statements_of_begin_statement(statement) 
        return result
    
    def __execute_print_statement(self, statement):
        out_str = ""
        out_stmt = statement[1:]
        for i in range(len(out_stmt)):
            if out_stmt[i] in self.obj_variables:
                out_str += str(self.obj_variables[out_stmt[i]].value_of())
            else:
                out_str += out_stmt[i]
            if i != len(out_stmt) - 1:
                out_str += ' '
        self.interpreter.output(out_str) 
        return 0
        # ! need to base on interpreter base class

    def __execute_input_statement(self, statement):
        self.obj_variables[statement[1]] = Value(self.interpreter.get_input())
        return 0

    def __execute_set_statement(self, statement):
        self.obj_variables[statement[1]] = Value(statement[2])
        return 0

    def __execute_call_statement(self, statement):
        pass

    def __execute_while_statement(self, statement):
        pass

    def __execute_if_statement(self, statement):
        pass
    
    def __execute_return_statement(self, statement):
        pass

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        statements = statement[1:]
        for i in statements:
            self.__run_statement(i)
        return 0

def is_a_print_statement(statement):
    return statement[0] == 'print'

def is_an_input_statement(statement):
    return statement[0] == 'inputi'

def is_a_set_statement(statement):
    return statement[0] == 'set'

def is_a_call_statement(statement):
    pass

def is_a_while_statement(statement):
    pass

def is_an_if_statement(statement):
    pass

def is_a_return_statement(statement):
    pass

def is_a_begin_statement(statement):
    return statement[0] == 'begin'

class Field:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        

class Method:
    def __init__(self, name, parameters, statements):
        self.name = name
        self.parameters = parameters
        self.statements = statements #! this may be a list of statements

    def get_top_level_statement(self):
        return self.statements

class Type(Enum):
    BOOL = 1
    INT = 2
    STRING = 3
    POINTER = 4
    NULL_POINTER = -1

class Value:
    "value class"
    def __init__(self, value):
        self.type = None
        self.value = None
        value = str(value)
        if value.isnumeric():
            self.type = Type.INT
            self.value = int(value)
        elif value == 'true' or value == 'false':
            self.type = Type.BOOL
            self.value = value
        elif value == 'null':
            self.type = Type.POINTER
            self.value = Type.NULL_POINTER
        else:
            self.type = Type.STRING
            self.value = value.strip('"')

    def type_of(self):
        return self.type

    def value_of(self):
        return self.value

def main():
    source_code = """
    (class main
 (field x "abc")
 (method main ()
  (begin
   (set x "def")
   (print x)
   (set x 20)
   (print x)
   (set x true)
   (print x)
  )
 )
)

    """.split('\n')
    
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