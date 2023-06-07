NO_VISUAL_CONTEXT_MESSAGE = "Sorry the data required to show this visual is not available yet"
NO_VISUAL_RESULT_MESSAGE = "Sorry the result required to show this visual is not available yet"
NO_VISUAL_METADATA_MESSAGE = "Sorry the information required to show this visual has not been calculated"

class InvalidData(Exception):
    """
    Data provided to the DataInput is invalid in some way.
    """
    pass

class ConversionError(InvalidData):
    """
    Unable to convert the input data to the correct type due to another exception.
    """
    def __init__(self, message, orig_exception, **kwargs):
        self.orig_exception = orig_exception
        kwargs["orig"] = orig_exception
        super().__init__(message + " [" + ", ".join([k + "=" + str(v) for k,v in kwargs.items()]) + "]")

    def __repr__(self):
        return


class ValidationError(InvalidData):
    """
    Data validation of data by cerberus has failed.
    """
    pass

class MissingValue(InvalidData):
    """
    A value is missing from the supplied data.
    """
    pass


class StepDataError(Exception):
    """
    Base class for errors related to unavailable or invalid step data.
    """
    @property
    def _message(self):
        return ""

    def __init__(self, journey, step_name, exception=None, message=None, **kwargs):
        self.step_name = step_name
        self.journey = journey
        self.kwargs = kwargs

        if not message:
            message = self._message

        if exception:
             message+=f" [exception:{exception}]"


        super().__init__(message)


class StepDataNotAvailable(StepDataError):
    """
    Error thrown when data is not available in a step. Should result in step status changing to 'WAITING'
    """
    @property
    def _message(self):
        return f"Data not available in step {self.step_name}"

class InvalidStepData(StepDataError):
    """
    Error thrown when data is invalid. Should result in step status changing to 'ERROR'
    """
    @property
    def _message(self):
        return f"Data invalid in step {self.step_name}"

class VisualDataMissing(Exception):
    """
    Error thrown when there are problems with data used to generate visuals.
    The scope determine which message is used.
    """
    def __init__(self, element, scope):
        if scope == "result":
            msg = NO_VISUAL_RESULT_MESSAGE
        elif scope == "metadata":
            msg = NO_VISUAL_METADATA_MESSAGE
        else:
            msg = NO_VISUAL_CONTEXT_MESSAGE

        self.element = element
        super().__init__(msg)



