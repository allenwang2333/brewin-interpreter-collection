from intbase import InterpreterBase, ErrorType
from bparser import BParser
from enum import Enum

class Interpreter(InterpreterBase):
    """Interpreter Class"""
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.all_classes = {} # dict: {key=class_name, value = class description}
        self.operations = {}
        self.operators = {'+', '-', '*', '/', '%', '==', '>=', '<=', '!=', '>', '<', '&', '|', '!'}
        

    def run(self, program_source):
        # first parse the program
        result, parsed_program = BParser.parse(program_source)
        if result == False:
            self.error(ErrorType.SYNTAX_ERROR, "invalid input")
        print(parsed_program) # ! delete this before submission
        self.__init_operations()
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

    def __init_operations(self):
        # inspired by laster year Carey's solution
        self.operations[Type.INT] = {
        '+': lambda a,b: Value(a.val()+b.val(), Type.INT),
        '-': lambda a,b: Value(a.val()-b.val(), Type.INT),
        '*': lambda a,b: Value(a.val()*b.val(), Type.INT),
        '/': lambda a,b: Value(a.val()/b.val(), Type.INT),
        '%': lambda a,b: Value(a.val()%b.val(), Type.INT),
        '==': lambda a,b: Value(a.val()==b.val(), Type.BOOL),
        '>=': lambda a,b: Value(a.val()>=b.val(), Type.BOOL),
        '<=': lambda a,b: Value(a.val()<=b.val(), Type.BOOL),
        '>': lambda a,b: Value(a.val()>b.val(), Type.BOOL),
        '<': lambda a,b: Value(a.val()<b.val(), Type.BOOL),
        '!=': lambda a,b: Value(a.val()!=b.val(), Type.BOOL),
        }
        self.operations[Type.BOOL] = {
        '!=': lambda a,b: Value(a.val()!=b.val(), Type.BOOL),
        '==': lambda a,b: Value(a.val()==b.val(), Type.BOOL),
        '&': lambda a,b: Value(a.val()&b.val(), Type.BOOL),
        '|': lambda a,b: Value(a.val()|b.val(), Type.BOOL),
        '!': lambda a: Value(not a.val(), Type.BOOL)
        }
        self.operations[Type.STRING] = {
        '+': lambda a,b: Value(a.val()+b.val(), Type.STRING),
        '==': lambda a,b: Value(a.val()==b.val(), Type.STRING),
        '!=': lambda a,b: Value(a.val()!=b.val(), Type.STRING)
        }


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
        self.method_variables = [] # stack frame

    def add_method(self, method):
        self.obj_methods[method[1]] = Method(method[1], method[2], method[3])

    def add_field(self, field):
        self.obj_variables[field[1]] = Value(field[2])

   # Interpret the specified method using the provided parameters    
    def run_method(self, method_name, parameters={}):
        self.method_variables.append(parameters)
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
            if isinstance(out_stmt[i], list):
                if out_stmt[i][0] == 'call':
                    out_str += self.__format_string(self.__execute_call_statement(out_stmt[i]))
                else:   
                    out_str += self.__format_string(self.__evaluate_expression(out_stmt[i]))
            elif out_stmt[i] in self.obj_variables:
                out_str += self.__format_string(self.obj_variables[out_stmt[i]])
            elif out_stmt[i] in self.method_variables[-1]:
                out_str += self.__format_string(self.method_variables[-1][out_stmt[i]])
            elif out_stmt[i][0] == '"' and out_stmt[i][-1] == '"':
                out_str += out_stmt[i].strip('"')
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
            if i != len(out_stmt) - 1:
                out_str += ' '
        self.interpreter.output(out_str) 
    
    def __format_string(self, string):
        if string.typeof() == Type.BOOL:
            if string.val():
                return 'true'
            else:
                return 'false'
        elif string.typeof() == Type.STRING:
            return string.val().strip('"')
        else:
            return str(string.val())

    def __execute_input_statement(self, statement):
        if statement[1] not in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
        self.obj_variables[statement[1]] = Value(self.interpreter.get_input())

    def __execute_set_statement(self, statement):
        if statement[1] not in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
        if isinstance(statement[2], list):
            if statement[2][0] == 'call':
                result = self.__execute_call_statement(statement[2])
            else:
                result = self.__evaluate_expression(statement[2])
            self.obj_variables[statement[1]] = result
        else:
            self.obj_variables[statement[1]] = Value(statement[2])

    def __execute_call_statement(self, statement):
        if statement[1] == 'me':
            local_variables = {}
            method = self.__find_method(statement[2])
            param_names = method.get_params()
            #result = self.__run_statement(statement)
            param_values = statement[3:]
            evaluated_values = []
            if len(param_values) != method.get_param_len():
                self.interpreter.error(ErrorType.TYPE_ERROR, "parameters does not match", statement[0].line_num)
            else:
                for i in range(len(param_values)):
                    if isinstance(param_values[i], list):
                        local_variables[param_names[i]] = self.__evaluate_expression(param_values[i])
                    else:
                        local_variables[param_names[i]] = Value(param_values[i])
                result = self.run_method(statement[2], local_variables)
                # for i in range(len(values)):
                #     del self.method_variables[method_params[i]]

                self.method_variables.pop()
            return result
        else:
            pass

    def __execute_while_statement(self, statement):
        if isinstance(statement[1], list):
            while (self.__evaluate_expression(statement[1]).val()):
                self.__run_statement(statement[2])
        elif statement[1] == 'true' or statement[1] == 'false':
            if statement[1] == 'true':
                while(True):
                    self.__run_statement(statement[2])
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in while statement", statement[0].line_num)

    def __execute_if_statement(self, statement):
        #print(statement)
        if isinstance(statement[1], list):
            eval_res = self.__evaluate_expression(statement[1])
            if (eval_res.val()):
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        elif statement[1] == 'true' or statement[1] == 'false':
            if statement[1] == 'true':
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in if statement", statement[0].line_num)

    
    def __execute_return_statement(self, statement):
        if len(statement) == 1:
            return None
        if isinstance(statement[1], list):
            if statement[1][0] == 'call':
                result = self.__execute_call_statement(statement[1])
            else:
                result = self.__evaluate_expression(statement[1])
        else:
            result = Value(statement[1])
        return result

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        statements = statement[1:]
        for i in statements:
            if is_a_return_statement(i):
                return self.__run_statement(i) 
            self.__run_statement(i)
        
    
    def __evaluate_expression(self, statement):
        stack = []
        if isinstance(statement, list):
            for i in statement:
                if isinstance(i, list):
                    if i[0] == 'call':
                        stack.append(self.__execute_call_statement(i))
                    else:
                        stack.append(self.__evaluate_expression(i))
                elif i in self.interpreter.operators:
                    stack.append(i)
                elif i in self.obj_variables:
                    stack.append(self.obj_variables[i])
                elif i in self.method_variables[-1]:
                    stack.append(self.method_variables[-1][i])
                else:
                    new_var = Value(i)
                    if new_var.typeof() == Type.UNDEFINED:
                        self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
                    else:
                        stack.append(new_var)
            if len(stack) == 3:
                b = stack.pop()
                a = stack.pop()
                operator = stack.pop()
                if operator not in self.interpreter.operators:
                    self.interpreter.error(ErrorType.SYNTAX_ERROR, "invalid operator", statement[0].line_num)
                if a.typeof() != b.typeof():
                    self.interpreter.error(ErrorType.TYPE_ERROR, "type does not match", statement[0].line_num)
                return self.interpreter.operations[a.typeof()][operator](a, b)
            elif len(stack) == 2:
                a = stack.pop()
                operator = stack.pop()
                if operator != '!':
                    self.interpreter.error(ErrorType.TYPE_ERROR, "wrong operator", statement[0].line_num)
                if a.typeof() != Type.BOOL:
                    self.interpreter.error(ErrorType.TYPE_ERROR, "non boolean", statement[0].line_num)
                return self.interpreter.operations[a.typeof()][operator](a)
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not an expression", statement[0].line_num)


def is_a_print_statement(statement):
    return statement[0] == 'print'

def is_an_input_statement(statement):
    return statement[0] == 'inputi'

def is_a_set_statement(statement):
    return statement[0] == 'set'

def is_a_call_statement(statement):
    return statement[0] == 'call'

def is_a_while_statement(statement):
    return statement[0] == 'while'

def is_an_if_statement(statement):
    return statement[0] == 'if'

def is_a_return_statement(statement):
    return statement[0] == 'return'

def is_a_begin_statement(statement):
    return statement[0] == 'begin'

class Method:
    def __init__(self, name, parameters, statements):
        self.name = name
        self.parameters = parameters
        self.statements = statements #! this may be a list of statements

    def get_top_level_statement(self):
        return self.statements
    
    def get_param_len(self):
        return len(self.parameters)

    def get_params(self):
        return self.parameters

class Type(Enum):
    BOOL = 1
    INT = 2
    STRING = 3
    POINTER = 4
    NULL_POINTER = 5
    UNDEFINED = -1

class Value:
    "value class"
    def __init__(self, value, type=None):
        if type == None:
            if value.isnumeric() or (value[0] == '-' and value[1:].isnumeric()):
                self.type = Type.INT
                self.value = int(value)
            elif value == 'true' or value == 'false':
                self.type = Type.BOOL
                if value == 'true':
                    self.value = True
                else:
                    self.value = False
            elif value == 'null':
                self.type = Type.POINTER
                self.value = None
            elif value[0] == '"' and value[-1] == '"':
                self.type = Type.STRING
                self.value = value
            else:
                self.type = Type.UNDEFINED
                self.value = -1
        else:
            if type == Type.INT:
                self.type = Type.INT
                self.value = int(value)
            if type == Type.BOOL:
                self.type = Type.BOOL
                self.value = value
    def typeof(self):
        return self.type

    def val(self):
        return self.value

def main():
    test_1 = """
    (class main
 (field x true)
 (field y false)
 (method main ()
  (print (! x))
 )
)
    """.split('\n')
    interpreter = Interpreter()
    interpreter.run(test_1)

if __name__ == '__main__':
    main()