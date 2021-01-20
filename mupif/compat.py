import Pyro5.serializers, Pyro5.core
import inspect
import copyreg

# copied from Pyro4 code
class PickleSerializer(Pyro5.serializers.SerializerBase):
    """
    A (de)serializer that wraps the Pickle serialization protocol.
    It can optionally compress the serialized data, and is thread safe.
    """
    serializer_id = 4  # never change this

    def dumpsCall(self, obj, method, vargs, kwargs):
        return pickle.dumps((obj, method, vargs, kwargs), config.PICKLE_PROTOCOL_VERSION)

    def dumps(self, data):
        return pickle.dumps(data, config.PICKLE_PROTOCOL_VERSION)

    def loadsCall(self, data):
        data = self._convertToBytes(data)
        return pickle.loads(data)

    def loads(self, data):
        data = self._convertToBytes(data)
        return pickle.loads(data)

    @classmethod
    def register_type_replacement(cls, object_type, replacement_function):
        def copyreg_function(obj):
            return replacement_function(obj).__reduce__()

        if object_type is type or not inspect.isclass(object_type):
            raise ValueError("refusing to register replacement for a non-type or the type 'type' itself")
        try:
            copyreg.pickle(object_type, copyreg_function)
        except TypeError:
            pass

# register pickle serializer with Pyro5
Pyro5.serializers.serializers['pickle']=PickleSerializer()

# API change for Pyro5
Pyro5.core.URI.asString=Pyro5.core.URI.__str__
