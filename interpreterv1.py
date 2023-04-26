from intbase import InterpreterBase, ErrorType
from bparser import BParser
from enum import Enum


class Interpreter(InterpreterBase):
    """Interpreter Class"""
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.all_classes = {}  # dict: {key=class_name, value = class description}
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
        for class_def in parsed_program:
            if class_def[1] not in self.all_classes and class_def[0] == self.CLASS_DEF:
                self.all_classes[class_def[1]] = ClassDefinition(class_def[1], class_def[2:], self)
            else:
                self.error(ErrorType.TYPE_ERROR, f"duplicate class name {class_def[1]} {class_def[1].line_num}")
            # ! check if the program has at least one class
            
    def __find_definition_for_class(self, class_name):
        if class_name in self.all_classes:
            return self.all_classes[class_name]
        else:
            self.error(ErrorType.NAME_ERROR, f"class {class_name} can't be found")

    def __init_operations(self):
        """
        Inspired by fall 22 Carey's solution on Apr 22 2023
        https://github.com/UCLA-CS-131/fall-22-proj-starter/blob/main/interpreterv1.py
        """
        self.operations[Type.INT] = {
            '+': lambda x,y: Value(x.val()+y.val(), Type.INT),
            '-': lambda x,y: Value(x.val()-y.val(), Type.INT),
            '*': lambda x,y: Value(x.val()*y.val(), Type.INT),
            '/': lambda x,y: Value(x.val()/y.val(), Type.INT),
            '%': lambda x,y: Value(x.val()%y.val(), Type.INT),
            '==': lambda x,y: Value(x.val()==y.val(), Type.BOOL),
            '>=': lambda x,y: Value(x.val()>=y.val(), Type.BOOL),
            '<=': lambda x,y: Value(x.val()<=y.val(), Type.BOOL),
            '>': lambda x,y: Value(x.val()>y.val(), Type.BOOL),
            '<': lambda x,y: Value(x.val()<y.val(), Type.BOOL),
            '!=': lambda x,y: Value(x.val()!=y.val(), Type.BOOL),
        }
        self.operations[Type.BOOL] = {
            '!=': lambda x,y: Value(x.val()!=y.val(), Type.BOOL),
            '==': lambda x,y: Value(x.val()==y.val(), Type.BOOL),
            '&': lambda x,y: Value(x.val()&y.val(), Type.BOOL),
            '|': lambda x,y: Value(x.val()|y.val(), Type.BOOL),
            '!': lambda x: Value(not x.val(), Type.BOOL)
        }
        self.operations[Type.STRING] = {
            '+': lambda x,y: Value(x.val()+y.val(), Type.STRING),
            '==': lambda x,y: Value(x.val()==y.val(), Type.BOOL),
            '!=': lambda x,y: Value(x.val()!=y.val(), Type.BOOL),
            '>=': lambda x,y: Value(x.val()>=y.val(), Type.BOOL),
            '<=': lambda x,y: Value(x.val()<=y.val(), Type.BOOL),
            '>': lambda x,y: Value(x.val()>y.val(), Type.BOOL),
            '<': lambda x,y: Value(x.val()<y.val(), Type.BOOL),
        }
        self.operations[Type.POINTER] = {
            '==': lambda x,y: Value(x.val() is y.val(), Type.BOOL),
            '!=': lambda x,y: Value(x.val() is not y.val(), Type.BOOL)
        }

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
        self.interpreter = interpreter
        self.obj_methods = {} # object methods
        self.obj_variables = {} # fields of object
        self.method_variables = [] # stack frame of variables

    def add_method(self, method):
        if method[1] in self.obj_methods:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate method")
        self.obj_methods[method[1]] = Method(method[1], method[2], method[3])

    def add_field(self, field):
        if field[1] in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate field")
        self.obj_variables[field[1]] = Value(field[2])

   # Interpret the specified method using the provided parameters    
    def run_method(self, method_name, parameters={}):
        self.method_variables.append(parameters)
        method = self.__find_method(method_name)
        statement = method.get_top_level_statement()
        result = self.__run_statement(statement)
        self.method_variables.pop()
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
            elif out_stmt[i] in self.method_variables[-1]:
                out_str += self.__format_string(self.method_variables[-1][out_stmt[i]])
            elif out_stmt[i] in self.obj_variables:
                out_str += self.__format_string(self.obj_variables[out_stmt[i]])

            # elif out_stmt[i][0] == '"' and out_stmt[i][-1] == '"':
            #     out_str += out_stmt[i].strip('"')
            # elif out_stmt[i][0] == '"' and out_stmt[i][-1] == '"':
            #     out_str += self.__format_string(Value(out_stmt[i]))    
            elif Value(out_stmt[i]).typeof() is not Type.UNDEFINED:
                out_str += self.__format_string(Value(out_stmt[i]))
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
        self.interpreter.output(out_str) 
    
    def __format_string(self, string):
        if string.typeof() == Type.BOOL:
            if string.val():
                return 'true'
            else:
                return 'false'
        elif string.typeof() == Type.STRING:
            return string.val().strip('"')
        elif string.typeof() == Type.RETURN:
            return 'None'
        else:
            return str(string.val())

    def __execute_input_statement(self, statement):
        if statement[1] not in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
        elif statement[0] == 'inputi':
            self.obj_variables[statement[1]] = Value(self.interpreter.get_input(), Type.INT)
        elif statement[0] == 'inputs':
            self.obj_variables[statement[1]] = Value(self.interpreter.get_input(), Type.STRING)

    def __execute_set_statement(self, statement):
        if statement[1] not in self.obj_variables and statement[1] not in self.method_variables[-1]:
            self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)

        if isinstance(statement[2], list):
            if statement[2][0] == 'call':
                result = self.__execute_call_statement(statement[2])
            else:
                result = self.__evaluate_expression(statement[2])
            
            if statement[1] in self.method_variables[-1]:
                self.method_variables[-1][statement[1]] = result
            elif statement[1] in self.obj_variables:
                self.obj_variables[statement[1]] = result
        else:
            if statement[1] in self.method_variables[-1]:
                if statement[2] in self.method_variables[-1]:
                    self.method_variables[-1][statement[1]] = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    self.method_variables[-1][statement[1]] = self.obj_variables[statement[2]]
                else:
                    self.method_variables[-1][statement[1]] = Value(statement[2])
            elif statement[1] in self.obj_variables:
                if statement[2] in self.method_variables[-1]:
                    self.obj_variables[statement[1]] = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    self.obj_variables[statement[1]] = self.obj_variables[statement[2]]
                else:
                    self.obj_variables[statement[1]] = Value(statement[2])

    def __execute_call_statement(self, statement):
        if statement[1][0] == 'new':
            local_variables = {}
            obj = self.__evaluate_expression(statement[1]).val()
            method = obj.__find_method(statement[2])
            param_names = method.get_params()
            param_values = statement[3:]
            if len(param_values) != method.get_param_len():
                self.interpreter.error(ErrorType.TYPE_ERROR, "parameters does not match", statement[0].line_num)
            else:
                for i in range(len(param_values)):
                    if isinstance(param_values[i], list):
                        local_variables[param_names[i]] = self.__evaluate_expression(param_values[i])
                    elif param_values[i] in self.method_variables[-1]:
                        local_variables[param_names[i]] = self.method_variables[-1][param_values[i]]
                    elif param_values[i] in self.obj_variables:
                        local_variables[param_names[i]] = self.obj_variables[param_values[i]]
                    else:
                        local_variables[param_names[i]] = Value(param_values[i])
                result = obj.run_method(statement[2], local_variables)
            return result
        elif statement[1] == 'me':
            local_variables = {}
            method = self.__find_method(statement[2])
            param_names = method.get_params()
            #result = self.__run_statement(statement)
            param_values = statement[3:]
            if len(param_values) != method.get_param_len():
                self.interpreter.error(ErrorType.TYPE_ERROR, "parameters does not match", statement[0].line_num)
            else:
                for i in range(len(param_values)):
                    if isinstance(param_values[i], list):
                        local_variables[param_names[i]] = self.__evaluate_expression(param_values[i])
                    elif param_values[i] in self.method_variables[-1]:
                        local_variables[param_names[i]] = self.method_variables[-1][param_values[i]]
                    elif param_values[i] in self.obj_variables:
                        local_variables[param_names[i]] = self.obj_variables[param_values[i]]
                    else:
                        local_variables[param_names[i]] = Value(param_values[i])
                result = self.run_method(statement[2], local_variables)
                # for i in range(len(values)):
                #     del self.method_variables[method_params[i]]
            return result
        elif statement[1] in self.obj_variables and isinstance(self.obj_variables[statement[1]].val(), ObjectDefinition):
            local_variables = {}
            obj_name = statement[1]
            obj = self.obj_variables[obj_name].val()
            method = obj.__find_method(statement[2])
            param_names = method.get_params()
            param_values = statement[3:]
            if len(param_values) != method.get_param_len():
                self.interpreter.error(ErrorType.TYPE_ERROR, "parameters does not match", statement[0].line_num)
            else:
                for i in range(len(param_values)):
                    if isinstance(param_values[i], list):
                        local_variables[param_names[i]] = self.__evaluate_expression(param_values[i])
                    elif param_values[i] in self.method_variables[-1]:
                        local_variables[param_names[i]] = self.method_variables[-1][param_values[i]]
                    elif param_values[i] in self.obj_variables:
                        local_variables[param_names[i]] = self.obj_variables[param_values[i]]
                    else:
                        local_variables[param_names[i]] = Value(param_values[i])
                result = obj.run_method(statement[2], local_variables)
            return result
        
        elif statement[1] in self.obj_variables and self.obj_variables[statement[1]].val() == None:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced a null value")
        else:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced illegal value")


    def __execute_while_statement(self, statement):
        result = None
        if isinstance(statement[1], list):
            while (self.__evaluate_expression(statement[1]).val()):
                result = self.__run_statement(statement[2])
                if isinstance(result, Value):
                    break
            return result
        elif statement[1] == 'true' or statement[1] == 'false':
            if statement[1] == 'true':
                while(True):
                    result = self.__run_statement(statement[2])
                    if isinstance(result, Value):
                        break
            return result
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
            return Value(None, Type.RETURN)
        if isinstance(statement[1], list):
            if statement[1][0] == 'call':
                result = self.__execute_call_statement(statement[1])
                if result is None:
                    return Value(None, Type.RETURN)
                return result
            else:
                result = self.__evaluate_expression(statement[1])
                if result is None:
                    return Value(None, Type.RETURN)
                return result
        elif statement[1] in self.obj_variables:
            result = self.obj_variables[statement[1]]
        elif statement[1] in self.method_variables[-1]:
            result = self.method_variables[-1][statement[1]]
        else:
            result = Value(statement[1])
        return result

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        statements = statement[1:]
        result = None
        for i in statements:
            result = self.__run_statement(i)
            # ! some problem here
            if not is_a_call_statement(i) and isinstance(result, Value):
                return result
        return result
    
    def __evaluate_expression(self, statement):
        stack = []
        if isinstance(statement, list):
            if statement[0] == 'call':
                return self.__execute_call_statement(statement)
            for i in statement:
                if isinstance(i, list):
                    if i[0] == 'call':
                        stack.append(self.__execute_call_statement(i))
                    else:
                        stack.append(self.__evaluate_expression(i))
                elif i == 'new':
                    stack.append('new')
                elif i in self.interpreter.all_classes:
                    stack.append(i)
                elif i in self.interpreter.operators:
                    stack.append(i)
                elif i in self.obj_variables:
                    stack.append(self.obj_variables[i])
                elif i in self.method_variables[-1]:
                    stack.append(self.method_variables[-1][i])
                else:
                    new_var = Value(i)
                    if new_var.typeof() == Type.UNDEFINED:
                        if len(stack) >= 1 and stack[-1] == 'new':
                            self.interpreter.error(ErrorType.TYPE_ERROR, "undefined class")
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
                if operator not in self.interpreter.operations[a.typeof()]:
                    self.interpreter.error(ErrorType.TYPE_ERROR, "incompatible operand")
                return self.interpreter.operations[a.typeof()][operator](a, b)
            elif len(stack) == 2:
                a = stack.pop()
                operator = stack.pop()
                if operator == '!':
                    if a.typeof() != Type.BOOL:
                        self.interpreter.error(ErrorType.TYPE_ERROR, "non boolean", statement[0].line_num)
                    if operator not in self.interpreter.operations[a.typeof()]:
                        self.interpreter.error(ErrorType.TYPE_ERROR, "incompatible operand")
                elif operator == 'new':
                    if a not in self.interpreter.all_classes:
                        self.interpreter.error(ErrorType.TYPE_ERROR, "undefined class")
                    else:
                        class_def = self.interpreter.all_classes[a]
                        obj = class_def.instantiate_object() 
                        return Value(obj, Type.POINTER)
                else:
                    self.interpreter.error(ErrorType.TYPE_ERROR, "operator error", statement[0].line_num)
                return self.interpreter.operations[a.typeof()][operator](a)
            
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not an expression", statement[0].line_num)


def is_a_print_statement(statement):
    return statement[0] == 'print'

def is_an_input_statement(statement):
    return (statement[0] == 'inputi') or (statement[0] == 'inputs')

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

def is_a_new_statement(statement):
    return statement[0] == 'new'

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
    UNDEFINED = -1
    RETURN = 0

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
                self.value = value.strip('"')
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
            if type == Type.STRING:
                self.type = Type.STRING
                self.value = str(value)
            if type == Type.POINTER:
                self.type = Type.POINTER
                self.value = value
            if type == Type.RETURN:
                self.type = Type.RETURN
                self.value = value
    def typeof(self):
        return self.type

    def val(self):
        return self.value

def main():
    test_1 = """
(class main
  (field foo_instance null)
  (method main ()
    (begin 
      (call me set_foo)
      (print (call foo_instance is_bar_negative))
      (print (call me print_concat "a" "b"))
    )
  )
  (method create_foo ()
    (return (new Foo))
  )
  (method set_foo ()
    (set foo_instance (call me create_foo))
  )

  (method print_concat (a b)
    (return (+ a b))
  )
)
(class Foo
  (field bar 1)
  (method is_bar_negative () (return (< bar 0)))
)

    """.split('\n')

    test_2 = """
    (class person
   (field name "")
   (field age 0)
   (method init (n a) (begin (set name n) (set age a)))
   (method talk (to_whom) (print name " says hello to " to_whom))
   (method get_age () (return age))
)

(class main
 (field p null)
 (method tell_joke (to_whom) (print "Hey " to_whom ", knock knock!"))
 (method main ()
   (begin
      (call me tell_joke "Leia")  # calling method in the current obj
      (set p (new person))    
      (call p init "Siddarth" (call me set_age))  # calling method in other object
      (call p talk "Boyan")        # calling method in other object
      (print "Siddarth's age is " (call p get_age))
   )
 )
 (method set_age ()
    (return 90)
 )
)


    """.split('\n')

    test_3 = """
(class main
  (field other null)
  (method main ()
    (begin
      (set other (new other_class))
      (print "Sum: " (+ (call (new other_class) add 3 7) (call (new other_class) add 5 5)))
      (call (new other_class) add 3 7)
    )
  )
)

(class other_class
  (method add (a b)
    (return (+ a b))
  )
)




    """.split('\n')

    test_4 = """
	(class main
  (field x 0)
  (field y 0)
  (method main ()
    (begin
      (set x 11)
      (set y 20)
      (call me check_sum x y)
      (call me check_product x y)
      (call me check_multiple x)
    )
  )
  (method check_sum (a b)
    (begin
      (if (== 0 (% (+ a b) 2))
        (print "Sum of x and y is even")
        (print "Sum of x and y is odd")
      )
    )
  )
  (method check_product (a b)
    (begin
      (if (& (== 0 (% a 2)) (== 0 (% b 2)))
        (print "Both x and y are even")
        (print "At least one of x and y is odd")
      )
    )
  )
  (method check_multiple (a)
    (begin
      (if (== 0 (% a 3))
        (print "x is a multiple of 3")
        (print "x is not a multiple of 3")
      )
      (if (== 0 (% a 5))
        (print "x is a multiple of 5")
        (print "x is not a multiple of 5")
      )
      (if (& (== 0 (% a 3)) (== 0 (% a 5)))
        (print "x is a multiple of both 3 and 5")
      )
    )
  )
)


    """.split('\n')
    interpreter = Interpreter()
    interpreter.run(test_3)

if __name__ == '__main__':
    main()