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
        self.type_match = {}
        self.default_return_val = {}
        self.class_relationships = {}
        

    def run(self, program_source):
        # first parse the program
        result, parsed_program = BParser.parse(program_source)
        if result == False:
            self.error(ErrorType.SYNTAX_ERROR, "invalid input")
        print(parsed_program) # ! delete this before submission
        self.__init_operations()
        self.__init_type_match()
        self.__init_default_return_val()
        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.__find_definition_for_class(self.MAIN_CLASS_DEF)
        obj = class_def.instantiate_object() 
        obj.run_method(InterpreterBase.MAIN_FUNC_DEF)
    
    def __discover_all_classes_and_track_them(self, parsed_program):
        # find all classes and put them is all_classes
        for class_def in parsed_program:
            if class_def[1] not in self.all_classes and class_def[0] == self.CLASS_DEF:
                class_definition = ClassDefinition(class_def[1], class_def[2:], self)
                self.class_relationships[class_def[1]] = class_definition.super_class
                self.all_classes[class_def[1]] = class_definition
                self.type_match[class_def[1]] = Type.POINTER
            else:
                self.error(ErrorType.NAME_ERROR, f"duplicate class name {class_def[1]} {class_def[1].line_num}")
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

    def __init_type_match(self):
        self.type_match['int'] = Type.INT
        self.type_match['string'] = Type.STRING
        self.type_match['bool'] = Type.BOOL
        self.type_match['void'] = Type.RETURN

    def __init_default_return_val(self):
        self.default_return_val[Type.INT] = Value(0, Type.INT)
        self.default_return_val[Type.BOOL] = Value(False, Type.BOOL)
        self.default_return_val[Type.STRING] = Value('', Type.STRING)
        self.default_return_val[Type.POINTER] = Value(None, Type.POINTER)


class ClassDefinition:
    def __init__(self, name, class_definition, interpreter):
        self.my_name = name
        self.my_class_definition = class_definition
        self.my_methods = [] # a list of description of methods
        self.my_fields = [] # ! can be optimized by hash table
        self.interpreter = interpreter
        self.super_class = None
        if len(self.my_class_definition) >= 2:
            if self.my_class_definition[0] == 'inherits':
                self.super_class = self.my_class_definition[1]
        for item in class_definition:
            if item[0] == 'field' and item not in self.my_fields:
                self.my_fields.append(item)
            elif item[0] == 'method' and item not in self.my_methods:
                self.my_methods.append(item)
            elif item in self.my_fields or item in self.my_methods:
                self.interpreter.error(ErrorType.NAME_ERROR, "duplicate names")

    # uses the definition of a class to create and return an instance of it
    def instantiate_object(self):
        obj = ObjectDefinition(self.interpreter)
        obj.class_name = self.my_name
        #! assume a class cannot inherit itself
        if self.super_class is not None:
            if self.super_class in self.interpreter.all_classes:
                class_def = self.interpreter.all_classes[self.super_class]
                obj.super_object = class_def.instantiate_object()
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'Base class not found')

        for method in self.my_methods:
            obj.add_method(method)

        for field in self.my_fields:
            obj.add_field(field)

        return obj


class ObjectDefinition:
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.class_name = None
        self.obj_methods = {} # object methods
        self.obj_variables = {} # fields of object
        self.method_variables = [] # stack frame of variables
        self.local_variables = [{}] # stack frame of local variables
        self.super_object = None

    def add_method(self, method):
        if method[2] in self.obj_methods:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate method")
        else:
            self.obj_methods[method[2]] = Method(method[1], method[2], method[3], method[4], self.interpreter)

    def add_field(self, field):
        if field[2] in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate field")
        temp_value = Value(field[3])
        if temp_value.typeof() != self.interpreter.type_match[field[1]]:
            self.interpreter.error(ErrorType.TYPE_ERROR, "invalid type")
        if temp_value.typeof() == Type.POINTER:
            temp_value.class_name = field[1]
        self.obj_variables[field[2]] = temp_value
   # Interpret the specified method using the provided parameters    
    def run_method(self, method_name, parameters={}, type_signature=[]):
        self.method_variables.append(parameters)
        method, calling_obj= self.__find_method(method_name, type_signature)
        statement = method.get_top_level_statement()
        result = calling_obj.__run_statement(statement)
        self.method_variables.pop()
        return result
    
    def __find_method(self, method_name, type_signature):
        if method_name in self.obj_methods and self.obj_methods[method_name].get_type_signature() == type_signature:
            return self.obj_methods[method_name], self
        elif method_name in self.obj_methods and len(self.obj_methods[method_name].get_type_signature()) == len(type_signature):
            method_type_signature = self.obj_methods[method_name].get_type_signature()
            flag = True
            for i in range(len(method_type_signature)):
                if isinstance(method_type_signature[i], tuple):
                    if not self.__find_class_name(method_type_signature[i][1], type_signature[i][1]):
                        flag = False
                else:
                    if method_type_signature[i] != type_signature[i]:
                        flag = False
            if flag:
                return self.obj_methods[method_name], self
            elif self.super_object is not None:
                return self.super_object.__find_method(method_name, type_signature)
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, "method undefined")
        elif self.super_object is not None:
            return self.super_object.__find_method(method_name, type_signature)
        else:
            self.interpreter.error(ErrorType.NAME_ERROR, "method undefined")

  # runs/interprets the passed-in statement until completion and 
  # gets the result, if any
    def __run_statement(self, statement):
        if statement[0] == InterpreterBase.PRINT_DEF:
            result = self.__execute_print_statement(statement)
        elif statement[0] == InterpreterBase.INPUT_INT_DEF or statement[0] == InterpreterBase.INPUT_STRING_DEF:
            result = self.__execute_input_statement(statement)
        elif statement[0] == InterpreterBase.SET_DEF:
            result = self.__execute_set_statement(statement)
        elif statement[0] == InterpreterBase.CALL_DEF:
            result = self.__execute_call_statement(statement)
        elif statement[0] == InterpreterBase.WHILE_DEF:
            result = self.__execute_while_statement(statement)
        elif statement[0] == InterpreterBase.IF_DEF:
            result = self.__execute_if_statement(statement)
        elif statement[0] == InterpreterBase.RETURN_DEF:
            result = self.__execute_return_statement(statement)
        elif statement[0] == InterpreterBase.LET_DEF:
            result = self.__execute_let_statements(statement)
        elif statement[0] == InterpreterBase.BEGIN_DEF:
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
            elif out_stmt[i] in self.local_variables[-1]:
                out_str += self.__format_string(self.local_variables[-1][out_stmt[i]])
            elif out_stmt[i] in self.method_variables[-1]:
                out_str += self.__format_string(self.method_variables[-1][out_stmt[i]])
            elif out_stmt[i] in self.obj_variables:
                out_str += self.__format_string(self.obj_variables[out_stmt[i]])  
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

        if statement[1] not in self.local_variables[-1]:
            if (statement[1] not in self.obj_variables) and (statement[1] not in self.method_variables[-1]):
                # ! there might be a problem with stack of super class
                self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)

        name = statement[1]
        if isinstance(statement[2], list):
            if statement[2][0] == 'call':
                result = self.__execute_call_statement(statement[2])
            else:
                result = self.__evaluate_expression(statement[2])
            if name in self.local_variables[-1]:
                self.__type_check(self.local_variables[-1][name], result)
                self.local_variables[-1][name] = result
            elif name in self.method_variables[-1]:
                self.__type_check(self.method_variables[-1][name], result)
                self.method_variables[-1][name] = result
            elif name in self.obj_variables:
                self.__type_check(self.obj_variables[name], result)
                self.obj_variables[name] = result
        else:
            if name in self.local_variables[-1]:
                if statement[2] in self.local_variables[-1]:
                    temp_value = self.local_variables[-1][statement[2]]
                elif statement[2] in self.method_variables[-1]:
                    temp_value = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    temp_value = self.obj_variables[statement[2]]
                else:
                    temp_value = Value(statement[2])
                    if temp_value.typeof() == Type.POINTER:
                        temp_value.class_name = self.local_variables[-1][name].class_name
                self.__type_check(self.local_variables[-1][name], temp_value)
                self.local_variables[-1][name] = temp_value
            elif name in self.method_variables[-1]:
                if statement[2] in self.local_variables[-1]:
                    temp_value = self.local_variables[-1][statement[2]]
                elif statement[2] in self.method_variables[-1]:
                    temp_value = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    temp_value = self.obj_variables[statement[2]]
                else:
                    temp_value = Value(statement[2])
                    if temp_value.typeof() == Type.POINTER:
                        temp_value.class_name = self.method_variables[-1][name].class_name
                self.__type_check(self.method_variables[-1][name], temp_value)
                self.method_variables[-1][name] = temp_value

            elif name in self.obj_variables:
                if statement[2] in self.local_variables[-1]:
                    temp_value = self.local_variables[-1][statement[2]]
                elif statement[2] in self.method_variables[-1]:
                    temp_value = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    temp_value = self.obj_variables[statement[2]]
                else:
                    temp_value = Value(statement[2])
                    if temp_value.typeof() == Type.POINTER:
                        temp_value.class_name = self.obj_variables[name].class_name

                self.__type_check(self.obj_variables[name], temp_value)
                self.obj_variables[name] = temp_value
                
    def __type_check(self, ref, other_ref):
        if ref.typeof() == other_ref.typeof():
            if ref.typeof() == Type.POINTER:
                if not self.__find_class_name(ref.class_name, other_ref.class_name):
                    self.interpreter.error(ErrorType.TYPE_ERROR, 'Assigning incompatible type')
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, 'Assigning incompatible type')


    def __execute_call_statement(self, statement):
        local_variables = {}
        method = None
        param_names = None
        param_values = None
        type_signature = []
        temp_list = []
        if statement[1][0] == 'new':
            obj = self.__evaluate_expression(statement[1]).val()
            param_values = statement[3:]
        elif statement[1] == 'me':
            obj = self
            param_values = statement[3:]
        elif statement[1] == 'super':
            obj = self.super_object
            param_values = statement[3:]
        elif statement[1] in self.obj_variables and isinstance(self.obj_variables[statement[1]].val(), ObjectDefinition):
            obj_name = statement[1]
            obj = self.obj_variables[obj_name].val()
            param_values = statement[3:]
        elif statement[1] in self.method_variables[-1] and isinstance(self.method_variables[-1][statement[1]].val(), ObjectDefinition):
            obj_name = statement[1]
            obj = self.method_variables[-1][obj_name].val()
            param_values = statement[3:]
        elif statement[1] in self.obj_variables and self.obj_variables[statement[1]].val() == None:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced a null value")
        else:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced illegal value")


        for i in range(len(param_values)):
            if isinstance(param_values[i], list):
                temp_value = self.__evaluate_expression(param_values[i])
            elif param_values[i] in self.method_variables[-1]:
                temp_value = self.method_variables[-1][param_values[i]]
            elif param_values[i] in self.obj_variables:
                temp_value = self.obj_variables[param_values[i]]
            else:
                temp_value = Value(param_values[i])
            temp_list.append(temp_value)
            if temp_value.typeof() == Type.POINTER:
                type_signature.append((temp_value.typeof(), temp_value.class_name))
            else:
                type_signature.append(temp_value.typeof())

        method, calling_obj = obj.__find_method(statement[2], type_signature)
        param_names = method.get_params()
        for j in range(len(param_names)):
            if temp_list[j].typeof() == Type.POINTER:
                if not self.__find_class_name(param_names[j][0], temp_list[j].class_name):
                    # test whether the class has such base class name
                    self.interpreter.error(ErrorType.TYPE_ERROR, 'Passing invalid class')
            local_variables[param_names[j][1]] = temp_list[j]

        result = calling_obj.run_method(statement[2], local_variables, type_signature)
            # ! need to deal with classes
        return_type = method.get_return_type()

        if result is None:
            if return_type != Type.RETURN:
                result = self.interpreter.default_return_val[return_type]
            if return_type == Type.POINTER:
                result.class_name = method.real_return_type
        elif result.typeof() == Type.RETURN and return_type != Type.RETURN:
            result = self.interpreter.default_return_val[return_type]
        elif result.typeof() != return_type:
            self.interpreter.error(ErrorType.TYPE_ERROR, 'invalid return type')
        elif result.typeof() == Type.POINTER and return_type == Type.POINTER:
            if result.val() is None:
                result.class_name = method.real_return_type
            if not self.__find_class_name(method.real_return_type, result.class_name):
                # test whether the class has such base class name
                self.interpreter.error(ErrorType.TYPE_ERROR, 'Returning invalid class')
        return result


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
            if eval_res.typeof() != Type.BOOL:
                self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in if statement")
            if eval_res.val():
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        elif statement[1] == 'true' or statement[1] == 'false':
            if statement[1] == 'true':
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        elif statement[1] in self.method_variables[-1] and self.method_variables[-1][statement[1]].typeof() == Type.BOOL:
            flag = self.method_variables[-1][statement[1]]
            if flag.typeof() != Type.BOOL:
                self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in if statement")
            if flag.val():
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        elif statement[1] in self.obj_variables and self.obj_variables[statement[1]].typeof() == Type.BOOL:
            flag = self.obj_variables[statement[1]]
            if flag.typeof() != Type.BOOL:
                self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in if statement")
            if flag.val():
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
        elif self.super_object is not None and statement[1] in self.super_object.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, 'Cant access private field of base class')
        elif statement[1] == 'me':
            result = Value(self, Type.POINTER)
            result.class_name = self.class_name
        else:
            result = Value(statement[1])

        return result

    def __execute_let_statements(self, statement):
        variables = statement[1]
        statements = statement[2:]
        let_variables = {}
        for i in range(len(variables)):
            if variables[i][1] in let_variables:
                self.interpreter.error(ErrorType.NAME_ERROR, 'Duplicate definition of local variables')
            if isinstance(variables[i][2], list):
                temp_value = self.__evaluate_expression(variables[i][2])
            else:
                temp_value = Value(variables[i][2])
                if temp_value.typeof() == Type.POINTER:
                    temp_value.class_name = variables[i][0]

            if temp_value.typeof() == self.interpreter.type_match[variables[i][0]]:
                if temp_value.typeof() == Type.POINTER:
                    if not self.__find_class_name(variables[i][0], temp_value.class_name):
                        self.interpreter.error(ErrorType.TYPE_ERROR, 'invalid types')
                let_variables[variables[i][1]] = temp_value
            else:
                self.interpreter.error(ErrorType.TYPE_ERROR, 'invalid types')
        self.local_variables.append(let_variables)
        for j in statements:
            result = self.__run_statement(j)
            # ! some problem here
            if j[0] != InterpreterBase.CALL_DEF and isinstance(result, Value):
                self.local_variables.pop()
                return result
        self.local_variables.pop()
        return result



    def __execute_all_sub_statements_of_begin_statement(self, statement):
        statements = statement[1:]
        result = None
        for i in statements:
            result = self.__run_statement(i)
            # ! some problem here
            if (i[0] != InterpreterBase.CALL_DEF) and isinstance(result, Value):
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
                if a.typeof() == Type.POINTER and (a.class_name is not None) and (b.class_name is not None):
                    if not self.__find_class_name(a.class_name, b.class_name):
                        if not self.__find_class_name(b.class_name, a.class_name):
                            self.interpreter.error(ErrorType.TYPE_ERROR, 'Incompatible types')
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
                        temp_value = Value(obj, Type.POINTER)
                        temp_value.class_name = a
                        return temp_value
                else:
                    self.interpreter.error(ErrorType.TYPE_ERROR, "operator error", statement[0].line_num)
                return self.interpreter.operations[a.typeof()][operator](a)
            
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not an expression", statement[0].line_num)

    def __find_class_name(self, base_name, derived_class):
        if base_name == derived_class:
            return True
        elif self.interpreter.class_relationships[derived_class] is None:
            return False
        else:
            return self.__find_class_name(base_name, self.interpreter.class_relationships[derived_class])

class Method:
    def __init__(self, return_type, name, parameters, statements, interpreter):
        self.interpreter = interpreter
        self.name = name
        self.parameters = parameters
        self.formal_parameters = []
        for i in parameters:
            if i[1] not in self.formal_parameters:
                self.formal_parameters.append(i[1])
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'duplicate formal parameters')
        self.statements = statements #! this may be a list of statements
        self.return_type = self.interpreter.type_match[return_type]
        self.type_signature = []
        self.primitive_types = {'int', 'bool', 'string'}
        self.__init_type_signature()
        self.real_return_type = return_type
        if return_type not in self.primitive_types and return_type not in self.interpreter.all_classes:
            if return_type != 'void':
                self.interpreter.error(ErrorType.TYPE_ERROR, f'Type {return_type} does not exist')


    def __init_type_signature(self):
        for i in self.parameters:
            if i[0] in self.primitive_types:
                self.type_signature.append(self.interpreter.type_match[i[0]])
            elif i[0] in self.interpreter.all_classes:
                self.type_signature.append((Type.POINTER, i[0]))
            else:
                self.interpreter.error(ErrorType.TYPE_ERROR, f'Type {i[0]} does not exist')

    def get_type_signature(self):
        return self.type_signature

    def get_top_level_statement(self):
        return self.statements
    
    def get_param_len(self):
        return len(self.parameters)

    def get_params(self):
        return self.parameters

    def get_return_type(self):
        return self.return_type

class Type(Enum):
    BOOL = 1
    INT = 2
    STRING = 3
    POINTER = 4
    UNDEFINED = -1
    RETURN = 0

class Value:
    "value class"
    def __init__(self, value, type=None, class_name=None):
        self.class_name = None # None if it's a primitive type

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
                self.class_name = class_name
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
 (method void foo ((string a) (int a))
  (print a b)
 )
 (method void main ()
   (call me foo "a" 10)
 )
)

    """.split('\n')
    test_4 = """
   (class main
  (field person pf null)
  (method void foo ((person p1) (student p2)) 
    (if (== p1 p2)   
      (print "same object")
      (print "diff object")
    )
  )
  (method void main ()
    (begin 
      (set pf (new person))
      (call me foo pf pf)
      (call me foo pf (new person))
    )
  )
)

(class person
  (field int x 10)
)
(class student inherits person
  (field int x 11)
)


""".split('\n')
    interpreter = Interpreter()
    interpreter.run(test_1)

if __name__ == '__main__':
    main()

# ! Need to implement:
# 1.call of other objects
# 2.inheritance
# 3.polymorphism
# 4.local vars