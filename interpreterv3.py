from intbase import InterpreterBase, ErrorType
from bparser import BParser
from enum import Enum
from copy import deepcopy


class Interpreter(InterpreterBase):
    """Interpreter Class"""
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)  # call InterpreterBase’s constructor
        self.all_classes = {}  # dict: {key=class_name, value = class description}
        self.all_template_classes = {} # dict: {key=template_class_name, value = template_class_description}
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
        print(parsed_program)  # ! delete this before submission
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
            if class_def[1] not in self.all_classes and class_def[0] == InterpreterBase.CLASS_DEF:
                class_definition = ClassDefinition(class_def[1], class_def[2:], self)
                self.class_relationships[class_def[1]] = class_definition.super_class
                self.all_classes[class_def[1]] = class_definition
                self.type_match[class_def[1]] = Type.POINTER
            elif class_def[0] == InterpreterBase.TEMPLATE_CLASS_DEF and class_def[1] not in self.all_template_classes:
                class_definition = ClassDefinition(class_def[1], class_def[3:], self)
                class_definition.parametrized_types = class_def[2]
                self.all_template_classes[class_def[1]] = class_definition
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
            '+': lambda x, y: Value(x.val() + y.val(), Type.INT),
            '-': lambda x, y: Value(x.val() - y.val(), Type.INT),
            '*': lambda x, y: Value(x.val() * y.val(), Type.INT),
            '/': lambda x, y: Value(x.val() / y.val(), Type.INT),
            '%': lambda x, y: Value(x.val() % y.val(), Type.INT),
            '==': lambda x, y: Value(x.val() == y.val(), Type.BOOL),
            '>=': lambda x, y: Value(x.val() >= y.val(), Type.BOOL),
            '<=': lambda x, y: Value(x.val() <= y.val(), Type.BOOL),
            '>': lambda x, y: Value(x.val() > y.val(), Type.BOOL),
            '<': lambda x, y: Value(x.val() < y.val(), Type.BOOL),
            '!=': lambda x, y: Value(x.val() != y.val(), Type.BOOL),
        }
        self.operations[Type.BOOL] = {
            '!=': lambda x, y: Value(x.val() != y.val(), Type.BOOL),
            '==': lambda x, y: Value(x.val() == y.val(), Type.BOOL),
            '&': lambda x, y: Value(x.val() & y.val(), Type.BOOL),
            '|': lambda x, y: Value(x.val() | y.val(), Type.BOOL),
            '!': lambda x: Value(not x.val(), Type.BOOL)
        }
        self.operations[Type.STRING] = {
            '+': lambda x, y: Value(x.val() + y.val(), Type.STRING),
            '==': lambda x, y: Value(x.val() == y.val(), Type.BOOL),
            '!=': lambda x, y: Value(x.val() != y.val(), Type.BOOL),
            '>=': lambda x, y: Value(x.val() >= y.val(), Type.BOOL),
            '<=': lambda x, y: Value(x.val() <= y.val(), Type.BOOL),
            '>': lambda x, y: Value(x.val() > y.val(), Type.BOOL),
            '<': lambda x, y: Value(x.val() < y.val(), Type.BOOL),
        }
        self.operations[Type.POINTER] = {
            '==': lambda x, y: Value(x.val() is y.val(), Type.BOOL),
            '!=': lambda x, y: Value(x.val() is not y.val(), Type.BOOL)
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
        self.my_methods = []  # a list of description of methods
        self.my_fields = []  # ! can be optimized by hash table
        self.interpreter = interpreter
        self.super_class = None
        self.exception = None
        self.parametrized_types = None
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
    def instantiate_object(self, param=None):
        obj = ObjectDefinition(self.interpreter)
        obj.class_name = self.my_name
        # ! assume a class cannot inherit itself
        if self.super_class is not None:
            if self.super_class in self.interpreter.all_classes:
                class_def = self.interpreter.all_classes[self.super_class]
                obj.super_object = class_def.instantiate_object()
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'Base class not found')

        for field in self.my_fields:
            if self.parametrized_types is not None:
                field = deepcopy(field)
                self.__search_and_replace(field, param)
            obj.add_field(field)

        for method in self.my_methods:
            if self.parametrized_types is not None:
                method = deepcopy(method)
                self.__search_and_replace(method, param)
            obj.add_method(method)

        return obj
    def __search_and_replace(self, lst, param):
        if len(lst) == 0:
            return
        for i in range(len(lst)):
            if isinstance(lst[i], list):
                self.__search_and_replace(lst[i], param)
            else:
                for j in range(len(self.parametrized_types)):
                    if lst[i] == self.parametrized_types[j]:
                        lst[i] = param[j]
                    elif lst[i].split('@')[0] in self.interpreter.all_template_classes:
                        lst[i] = lst[i].replace(self.parametrized_types[j], param[j])

class ObjectDefinition:
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.class_name = None
        self.obj_methods = {}  # object methods
        self.obj_variables = {}  # fields of object
        self.method_variables = []  # stack frame of variables
        self.local_variables = [{}]  # stack frame of local variables
        self.super_object = None
        self.original_calling_object = self

    def add_method(self, method):
        if method[2] in self.obj_methods:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate method")
        else:
            self.obj_methods[method[2]] = Method(method[1], method[2], method[3], method[4], self.interpreter)

    def add_field(self, field):
        if field[2] in self.obj_variables:
            self.interpreter.error(ErrorType.NAME_ERROR, "duplicate field")
        if field[1].split('@')[0] in self.interpreter.all_template_classes:
            self.__check_template_class(field[1])
        if len(field) == 4:
            temp_value = Value(field[3])
        else:
            temp_type = self.interpreter.type_match[field[1]]
            val = self.interpreter.default_return_val[temp_type].val()
            temp_value = Value(val, temp_type)
        if temp_value.typeof() != self.interpreter.type_match[field[1]]:
            self.interpreter.error(ErrorType.TYPE_ERROR, "invalid type")
        if temp_value.typeof() == Type.POINTER:
            temp_value.class_name = field[1]
            temp_value.original_class_name = field[1]
        self.obj_variables[field[2]] = temp_value

    # Interpret the specified method using the provided parameters
    def run_method(self, method_name, parameters={}, type_signature=[]):
        self.method_variables.append(parameters)
        method, calling_obj = self.__find_method(method_name, type_signature)
        statement = method.get_top_level_statement()
        result = calling_obj.__run_statement(statement)
        self.method_variables.pop()
        return result

    def __find_method(self, method_name, type_signature):
        if method_name in self.obj_methods and self.obj_methods[method_name].get_type_signature() == type_signature:
            return self.obj_methods[method_name], self
        elif method_name in self.obj_methods and len(self.obj_methods[method_name].get_type_signature()) == len(
                type_signature):
            method_type_signature = self.obj_methods[method_name].get_type_signature()
            flag = True
            for i in range(len(method_type_signature)):
                if isinstance(method_type_signature[i], tuple) and isinstance(type_signature[i], tuple):
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
        elif statement[0] == InterpreterBase.THROW_DEF:
            result = self.__execute_throw_statement(statement)
        elif statement[0] == InterpreterBase.TRY_DEF:
            result = self.__execute_try_statement(statement)
        return result

    def __execute_print_statement(self, statement):
        out_str = ""
        out_stmt = statement[1:]
        for i in range(len(out_stmt)):
            if isinstance(out_stmt[i], list):
                if out_stmt[i][0] == 'call':
                    result = self.__execute_call_statement(out_stmt[i])
                    if result is not None and result.typeof() == Type.ERROR:
                        return result
                    out_str += self.__format_string(result)
                else:
                    result = self.__evaluate_expression(out_stmt[i])
                    if result is not None and result.typeof() == Type.ERROR:
                        return result
                    out_str += self.__format_string(result)
            elif self.__find_local_variables(out_stmt[i]) is not None:
                index = self.__find_local_variables(out_stmt[i])
                out_str += self.__format_string(self.local_variables[index][out_stmt[i]])
            elif out_stmt[i] in self.method_variables[-1]:
                out_str += self.__format_string(self.method_variables[-1][out_stmt[i]])
            elif out_stmt[i] in self.obj_variables:
                out_str += self.__format_string(self.obj_variables[out_stmt[i]])
            elif Value(out_stmt[i]).typeof() is not Type.UNDEFINED:
                out_str += self.__format_string(Value(out_stmt[i]))
            elif out_stmt[i] == InterpreterBase.EXCEPTION_VARIABLE_DEF and self.exception is not None:
                out_str += self.__format_string(self.exception)
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)
        self.interpreter.output(out_str)

    def __find_local_variables(self, name):
        size = len(self.local_variables)
        for i in range(size - 1, -1, -1):
            if name in self.local_variables[i]:
                return i
        return None

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

        if self.__find_local_variables(statement[1]) is None:
            if (statement[1] not in self.obj_variables) and (statement[1] not in self.method_variables[-1]):
                # ! there might be a problem with stack of super class
                    if statement[1] != InterpreterBase.EXCEPTION_VARIABLE_DEF:
                        self.interpreter.error(ErrorType.NAME_ERROR, "undefined variable", statement[0].line_num)

        name = statement[1]
        if isinstance(statement[2], list):
            if statement[2][0] == 'call':
                result = self.__execute_call_statement(statement[2])
            else:
                result = self.__evaluate_expression(statement[2])
            if result is not None and result.typeof() == Type.ERROR:
                return result
            if name == InterpreterBase.EXCEPTION_VARIABLE_DEF:
                if self.exception is None:
                    self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                self.__type_check(self.exception, result)
                self.exception = result
            elif self.__find_local_variables(name) is not None:
                index = self.__find_local_variables(name)
                self.__type_check(self.local_variables[index][name], result)
                self.local_variables[index][name] = result
            elif name in self.method_variables[-1]:
                self.__type_check(self.method_variables[-1][name], result)
                self.method_variables[-1][name] = result
            elif name in self.obj_variables:
                # self.__type_check(self.obj_variables[name], result)
                if self.obj_variables[name].typeof() == result.typeof():
                    if self.obj_variables[name].typeof() == Type.POINTER:
                        if not self.__find_class_name(self.obj_variables[name].class_name, result.class_name):
                            if not self.__find_class_name(self.obj_variables[name].original_class_name,
                                                          result.class_name):
                                self.interpreter.error(ErrorType.TYPE_ERROR, 'Assigning incompatible type')
                else:
                    self.interpreter.error(ErrorType.TYPE_ERROR, 'Assigning incompatible type')
                orig_class_name = self.obj_variables[name].original_class_name
                self.obj_variables[name] = result
                self.obj_variables[name].original_class_name = orig_class_name
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'invalid variable name')
        else:
            if name == InterpreterBase.EXCEPTION_VARIABLE_DEF:
                if self.exception is None:
                    self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                if statement[2] == InterpreterBase.EXCEPTION_VARIABLE_DEF:
                    temp_value = self.exception
                elif self.__find_local_variables(statement[2]) is not None:
                    index = self.__find_local_variables(statement[2])
                    temp_value = self.local_variables[index][statement[2]]
                elif statement[2] in self.method_variables[-1]:
                    temp_value = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    temp_value = self.obj_variables[statement[2]]
                else:
                    temp_value = Value(statement[2])
                self.__type_check(self.exception, temp_value)
                self.exception = temp_value
            elif self.__find_local_variables(name) is not None:
                index = self.__find_local_variables(name)
                if statement[2] == 'exception':
                    if self.exception is None:
                        self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                    else:
                        temp_value = self.exception
                elif self.__find_local_variables(statement[2]) is not None:
                    second_index = self.__find_local_variables(statement[2])
                    temp_value = self.local_variables[second_index][statement[2]]
                elif statement[2] in self.method_variables[-1]:
                    temp_value = self.method_variables[-1][statement[2]]
                elif statement[2] in self.obj_variables:
                    temp_value = self.obj_variables[statement[2]]
                else:
                    temp_value = Value(statement[2])
                    if temp_value.typeof() == Type.POINTER:
                        temp_value.class_name = self.local_variables[index][name].class_name
                self.__type_check(self.local_variables[index][name], temp_value)
                self.local_variables[index][name] = temp_value
            elif name in self.method_variables[-1]:
                if statement[2] == 'exception':
                    if self.exception is None:
                        self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                    else:
                        temp_value = self.exception
                elif self.__find_local_variables(statement[2]) is not None:
                    index = self.__find_local_variables(statement[2])
                    temp_value = self.local_variables[index][statement[2]]
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
                if statement[2] == 'exception':
                    if self.exception is None:
                        self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                    else:
                        temp_value = self.exception
                elif self.__find_local_variables(statement[2]) is not None:
                    index = self.__find_local_variables(statement[2])
                    temp_value = self.local_variables[index][statement[2]]
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
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'invalid variable name')

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
        if statement[1][0] == 'call':
            obj = self.__execute_call_statement(statement[1]).val()
            param_values = statement[3:]
        elif statement[1][0] == 'new':
            obj = self.__evaluate_expression(statement[1]).val()
            param_values = statement[3:]
        elif statement[1] == 'me':
            obj = self.original_calling_object
            param_values = statement[3:]
        elif statement[1] == 'super':
            obj = self.super_object
            param_values = statement[3:]
        elif self.__find_local_variables(statement[1]) is not None and isinstance(
                self.local_variables[self.__find_local_variables(statement[1])][statement[1]].val(), ObjectDefinition):
            index = self.__find_local_variables(statement[1])
            obj_name = statement[1]
            obj = self.local_variables[index][obj_name].val()
            param_values = statement[3:]
        elif statement[1] in self.method_variables[-1] and isinstance(self.method_variables[-1][statement[1]].val(),
                                                                      ObjectDefinition):
            obj_name = statement[1]
            obj = self.method_variables[-1][obj_name].val()
            param_values = statement[3:]
        elif statement[1] in self.obj_variables and isinstance(self.obj_variables[statement[1]].val(),
                                                               ObjectDefinition):
            obj_name = statement[1]
            obj = self.obj_variables[obj_name].val()
            param_values = statement[3:]
        elif statement[1] in self.obj_variables and self.obj_variables[statement[1]].val() == None:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced a null value")
        else:
            self.interpreter.error(ErrorType.FAULT_ERROR, "referenced illegal value")

        for i in range(len(param_values)):
            if isinstance(param_values[i], list):
                temp_value = self.__evaluate_expression(param_values[i])
                if temp_value is not None and temp_value.typeof() == Type.ERROR:
                    return temp_value
            elif param_values[i] == InterpreterBase.EXCEPTION_VARIABLE_DEF:
                if self.exception is not None:
                    temp_value = self.exception
                else:
                    self.interpreter.error(ErrorType.NAME_ERROR, 'Exception undefined')
            elif self.__find_local_variables(param_values[i]) is not None:
                index = self.__find_local_variables(param_values[i])
                temp_value = self.local_variables[index][param_values[i]]
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
                if temp_list[j].val() is None and temp_list[j].class_name is None:
                    temp_list[j].class_name = param_names[j][0]
            local_variables[param_names[j][1]] = temp_list[j]

        calling_obj.original_calling_object = obj
        result = calling_obj.run_method(statement[2], local_variables, type_signature)
        # ! need to deal with classes
        return_type = method.get_return_type()

        if result is not None and result.typeof() == Type.ERROR:
            return result
        if result is None:
            if return_type != Type.RETURN:
                result_val = self.interpreter.default_return_val[return_type].val()
                result_type = self.interpreter.default_return_val[return_type].typeof()
                result = Value(result_val, result_type)
            if return_type == Type.POINTER:
                result.class_name = method.real_return_type
            if return_type == Type.RETURN:
                result = Value(None, Type.RETURN)
        elif result.typeof() == Type.RETURN and return_type != Type.RETURN:
            result_val = self.interpreter.default_return_val[return_type].val()
            result_type = self.interpreter.default_return_val[return_type].typeof()
            result = Value(result_val, result_type)
            if return_type == Type.POINTER:
                result.class_name = method.real_return_type
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
            result = self.__evaluate_expression(statement[1])
            if result is not None and result.typeof() == Type.ERROR:
                return result
            while (self.__evaluate_expression(statement[1]).val()):
                result = self.__run_statement(statement[2])
                if isinstance(result, Value):
                    break
            return result
        elif statement[1] == 'true' or statement[1] == 'false':
            if statement[1] == 'true':
                while (True):
                    result = self.__run_statement(statement[2])
                    if isinstance(result, Value):
                        break
            return result
        elif self.__find_local_variables(statement[1]) is not None and \
                self.local_variables[self.__find_local_variables(statement[1])][statement[1]].typeof() == Type.BOOL:
            index = self.__find_local_variables(statement[1])
            while (self.local_variables[index][statement[1]].val()):
                result = self.__run_statement(statement[2])
                if isinstance(result, Value):
                    break
            return result
        elif statement[1] in self.method_variables[-1] and self.method_variables[-1][
            statement[1]].typeof() == Type.BOOL:
            while (self.method_variables[-1][statement[1]].val()):
                result = self.__run_statement(statement[2])
                if isinstance(result, Value):
                    break
            return result
        elif statement[1] in self.obj_variables and self.obj_variables[statement[1]].typeof() == Type.BOOL:
            while (self.obj_variables[statement[1]].val()):
                result = self.__run_statement(statement[2])
                if isinstance(result, Value):
                    break
            return result
        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in while statement", statement[0].line_num)

    def __execute_if_statement(self, statement):
        # print(statement)
        if isinstance(statement[1], list):
            eval_res = self.__evaluate_expression(statement[1])
            if eval_res is not None and eval_res.typeof() == Type.ERROR:
                return eval_res
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
        elif self.__find_local_variables(statement[1]) is not None and \
                self.local_variables[self.__find_local_variables(statement[1])][statement[1]].typeof() == Type.BOOL:
            index = self.__find_local_variables(statement[1])
            flag = self.local_variables[index][statement[1]]
            if flag.typeof() != Type.BOOL:
                self.interpreter.error(ErrorType.TYPE_ERROR, "not boolean in if statement")
            if flag.val():
                return self.__run_statement(statement[2])
            elif len(statement) > 3:
                return self.__run_statement(statement[3])
        elif statement[1] in self.method_variables[-1] and self.method_variables[-1][
            statement[1]].typeof() == Type.BOOL:
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
                elif result is not None and result.typeof() == Type.ERROR:
                    return result
                return result
            else:
                result = self.__evaluate_expression(statement[1])
                if result is not None and result.typeof() == Type.ERROR:
                    return result
                if result is None:
                    return Value(None, Type.RETURN)
                return result
        elif self.__find_local_variables(statement[1]) is not None:
            index = self.__find_local_variables(statement[1])
            result = self.local_variables[index][statement[1]]
        elif statement[1] in self.method_variables[-1]:
            result = self.method_variables[-1][statement[1]]
        elif statement[1] in self.obj_variables:
            result = self.obj_variables[statement[1]]
        elif statement[1] == 'me':
            result = Value(self.original_calling_object, Type.POINTER)
            result.class_name = self.class_name
        elif statement[1] == 'exception':
            if self.exception is not None:
                return self.exception
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
        else:
            result = Value(statement[1])
            if result.typeof() == Type.UNDEFINED:
                self.interpreter.error(ErrorType.NAME_ERROR, "Undefined variable")
        return result

    def __check_template_class(self, name):
        param_type = name.split('@')
        if param_type[0] not in self.interpreter.all_template_classes:
            self.interpreter.error(ErrorType.TYPE_ERROR, 'Template class does not exist')
        if len(param_type) - 1 != len(self.interpreter.all_template_classes[param_type[0]].parametrized_types):
            self.interpreter.error(ErrorType.TYPE_ERROR, 'Invalid parametrized types')
        for j in param_type[1:]:
            if j not in self.interpreter.type_match:
                self.interpreter.error(ErrorType.TYPE_ERROR, 'Parametrized type does not exist')
        if name not in self.interpreter.type_match:
            self.interpreter.type_match[name] = Type.POINTER

    def __execute_let_statements(self, statement):
        variables = statement[1]
        statements = statement[2:]
        let_variables = {}
        for i in range(len(variables)):
            if variables[i][1] in let_variables:
                self.interpreter.error(ErrorType.NAME_ERROR, 'Duplicate definition of local variables')
            else:
                if variables[i][0].split('@')[0] in self.interpreter.all_template_classes:
                    self.__check_template_class(variables[i][0])
                if len(variables[i]) == 3:
                    temp_value = Value(variables[i][2])
                else:
                    temp_type = self.interpreter.type_match[variables[i][0]]
                    val = self.interpreter.default_return_val[temp_type].val()
                    temp_value = Value(val, temp_type)
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
            # if result is not None and result.typeof() == Type.ERROR:
            #     self.local_variables.pop()
            #     return result
            if j[0] != InterpreterBase.CALL_DEF and isinstance(result, Value):
                self.local_variables.pop()
                return result
            if (j[0] == InterpreterBase.CALL_DEF) and isinstance(result, Value):
                if result.typeof() == Type.ERROR:
                    self.local_variables.pop()
                    return result
        self.local_variables.pop()
        return result

    def __execute_try_statement(self, statement):
        result = self.__run_statement(statement[1])
        if result is not None and result.typeof() == Type.ERROR:
            self.exception = result.val()
            result = self.__run_statement(statement[2])
            self.exception = None
            return result

    def __execute_all_sub_statements_of_begin_statement(self, statement):
        statements = statement[1:]
        result = None
        for i in statements:
            result = self.__run_statement(i)
            # ! some problem here
            # if isinstance(result, Value) and result.typeof() == Type.ERROR:
            #     return result
            if (i[0] != InterpreterBase.CALL_DEF) and isinstance(result, Value):
                return result
            if (i[0] == InterpreterBase.CALL_DEF) and isinstance(result, Value):
                if result.typeof() == Type.ERROR:
                    return result
        return result

    def __execute_throw_statement(self, statement):
        if isinstance(statement[1], list):
            err_msg = self.__evaluate_expression(statement[1])
            if err_msg is not None and err_msg.typeof() == Type.ERROR:
                return err_msg
        else:
            if statement[1] == InterpreterBase.EXCEPTION_VARIABLE_DEF:
                if self.exception is None:
                    self.interpreter.error(ErrorType.NAME_ERROR, 'Undefined exception')
                else:
                    err_msg = self.exception
            elif self.__find_local_variables(statement[1]) is not None:
                index = self.__find_local_variables(statement[1])
                err_msg = self.local_variables[index][statement[1]]
            elif statement[1] in self.method_variables:
                err_msg = self.method_variables[statement[1]]
            elif statement[1] in self.obj_variables:
                err_msg = self.obj_variables[statement[1]]
            else:
                err_msg = Value(statement[1])
        if err_msg.typeof() != Type.STRING:
            self.interpreter.error(ErrorType.TYPE_ERROR, 'Not a string in throw')
        return Value(err_msg, Type.ERROR)
    def __evaluate_expression(self, statement):
        stack = []
        if isinstance(statement, list):
            if statement[0] == 'call':
                return self.__execute_call_statement(statement)

            for i in statement:
                if isinstance(i, list):
                    if i[0] == 'call':
                        result = self.__execute_call_statement(i)
                    else:
                        result = self.__evaluate_expression(i)
                    if result is not None and result.typeof() == Type.ERROR:
                        return result
                    stack.append(result)
                elif i == 'new':
                    stack.append('new')
                elif i == 'me':
                    stack.append(Value(self, Type.POINTER))
                    stack[-1].class_name = self.class_name
                elif i == 'exception':
                    if self.exception is None:
                        self.interpreter.error(ErrorType.NAME_ERROR, 'No exception')
                    else:
                        stack.append(self.exception)
                elif i in self.interpreter.all_classes:
                    stack.append(i)
                elif i.split('@')[0] in self.interpreter.all_template_classes:
                    self.__check_template_class(i)
                    stack.append(i)
                elif i in self.interpreter.operators:
                    stack.append(i)
                elif self.__find_local_variables(i) is not None:
                    index = self.__find_local_variables(i)
                    stack.append(self.local_variables[index][i])
                elif i in self.method_variables[-1]:
                    stack.append(self.method_variables[-1][i])
                elif i in self.obj_variables:
                    stack.append(self.obj_variables[i])
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
                    if a in self.interpreter.all_classes:
                        class_def = self.interpreter.all_classes[a]
                        obj = class_def.instantiate_object()
                        temp_value = Value(obj, Type.POINTER)
                        temp_value.class_name = a
                        temp_value.original_class_name = a
                        return temp_value
                    elif (a.split('@')[0]) in self.interpreter.all_template_classes:
                        param = a.split('@')
                        class_def = self.interpreter.all_template_classes[param[0]]
                        obj = class_def.instantiate_object(param[1:])
                        temp_value = Value(obj, Type.POINTER)
                        temp_value.class_name = a
                        return temp_value
                    else:
                        self.interpreter.error(ErrorType.TYPE_ERROR, "Undefined class")

                else:
                    self.interpreter.error(ErrorType.TYPE_ERROR, "operator error", statement[0].line_num)
                return self.interpreter.operations[a.typeof()][operator](a)

        else:
            self.interpreter.error(ErrorType.TYPE_ERROR, "not an expression", statement[0].line_num)

    def __find_class_name(self, base_name, derived_class):
        if base_name == derived_class:
            return True
        elif derived_class is None:
            return True
        elif derived_class not in self.interpreter.class_relationships:
            return False
        elif self.interpreter.class_relationships[derived_class] is None:
            return False
        else:
            return self.__find_class_name(base_name, self.interpreter.class_relationships[derived_class])

    def check_template_class(self, name):
        self.__check_template_class(name)

class Method:
    def __init__(self, return_type, name, parameters, statements, interpreter):
        self.interpreter = interpreter
        self.name = name
        self.parameters = parameters
        self.formal_parameters = []
        self.primitive_types = {'int', 'bool', 'string'}
        if return_type not in self.primitive_types and return_type not in self.interpreter.all_classes:
            if return_type != 'void':
                if return_type.split('@')[0] not in self.interpreter.all_template_classes:
                    self.interpreter.error(ErrorType.TYPE_ERROR, f'Type {return_type} does not exist')
                else:
                    ObjectDefinition(interpreter).check_template_class(return_type)
        for i in parameters:
            if i[1] not in self.formal_parameters:
                self.formal_parameters.append(i[1])
            else:
                self.interpreter.error(ErrorType.NAME_ERROR, 'duplicate formal parameters')
        self.statements = statements  # ! this may be a list of statements

        self.type_signature = []

        self.__init_type_signature()
        self.real_return_type = return_type
        self.return_type = self.interpreter.type_match[return_type]

    def __init_type_signature(self):
        for i in self.parameters:
            if i[0] in self.primitive_types:
                self.type_signature.append(self.interpreter.type_match[i[0]])
            elif i[0] in self.interpreter.all_classes:
                self.type_signature.append((Type.POINTER, i[0]))
            elif i[0].split('@')[0] in self.interpreter.all_template_classes:
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
    ERROR = 5


class Value:
    "value class"

    def __init__(self, value, type=None, class_name=None):
        self.class_name = None  # None if it's a primitive type
        self.original_class_name = None

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
                self.original_class_name = class_name
            if type == Type.RETURN:
                self.type = Type.RETURN
                self.value = value
            if type == Type.ERROR:
                self.type = Type.ERROR
                self.value = value

    def typeof(self):
        return self.type

    def val(self):
        return self.value


def main():
    test_1 = """
    (tclass node (field_type)
  (field node@field_type next null)
  (field field_type value)
  (method void set_val ((field_type v)) (set value v))
  (method field_type get_val () (return value))
  (method void set_next((node@field_type n)) (set next n))
  (method node@field_type get_next() (return next))
)

(class main
  (method void main () 
    (let ((node@int x null))
      (set x (new node@int))
      (call x set_val 5)
      (print (call x get_val))
    )
  )
)

    """.split('\n')
    test_2 = """
    (tclass Foo (field_type)
  (method void chatter ((field_type x)) 
    (call x quack)         # line A
  )
  (method bool compare_to_5 ((field_type x))
    (return (== x 5))
  )
)
(class Duck
 (method void quack () (print "quack"))
)
(class main
  (field Foo@Duck t1)
  (field Foo@int t2)
  (method void main () 
    (begin
       (set t1 (new Foo@Duck))	# works fine
       (set t2 (new Foo@int))		# works fine

       (call t1 chatter (new Duck))	# works fine - ducks can talk
       (print (call t2 compare_to_5 5) ) 	# works fine - ints can be compared
       (call t1 chatter 10)  # generates a name error on line A (not a type error)
    )
  )
)

    """.split('\n')

    test_3 = """
(tclass MyTemplatedClass (shape_type animal_type)
  (field shape_type some_shape)
  (field animal_type some_animal)
  	  (method void act ((shape_type s) (animal_type a))
          (begin
            (print "Shape's area: " (call s get_area))
            (print "Animal's name: " (call a get_name))
          )
        ) 
      )
      
(class main
  (field MyTemplatedClass@string@int a)
  (field MyTemplatedClass@int@string b)
  (method void main ()
    (begin 
      (set b (call me bar null))
    )
  )
  (method MyTemplatedClass@int@string bar ((MyTemplatedClass@string@bool x))
    (begin
    (set x null)
    (return (new MyTemplatedClass@int@string))
    )
  )
)
""".split('\n')
    test_4 = """
(class main
 (field int x 0)
 (method void main ()
  (while (< x 2)
    (begin 
     (print x)
     (set x (+ x 1))
   )
  )
  (while false 
   (print x)
  )
  (while (< x 0)
   (print x)
  )
 )
)



    """.split('\n')
    interpreter = Interpreter()
    interpreter.run(test_4)


if __name__ == '__main__':
    main()

# Need to finish:
# templates
# error handling of some fields