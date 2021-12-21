import copy
import warnings
from torch.utils.data import IterDataPipe


class IterableWrapperIterDataPipe(IterDataPipe):
    r""":class:`IterableWrapperIterDataPipe`.

    Iterable datapipe that wraps an iterable object.

    Args:
        iterable: Iterable object to be wrapped into an IterDataPipe
        deepcopy: Option to deepcopy input iterable object for each
            iterator. The copy is made when the first element is read in iter().

    .. note::
      If `deepcopy` is set to False explicitly, users should ensure
      that data pipeline doesn't contain any in-place operations over
      the iterable instance, in order to prevent data inconsistency
      across iterations.
    """
    def __init__(self, iterable, deepcopy=True):
        self.iterable = iterable
        self.deepcopy = deepcopy
        self.state_counter = 0
        self.iter = None

    def __iter__(self):
        source_data = self.iterable
        if self.deepcopy:
            try:
                source_data = copy.deepcopy(self.iterable)
            # For the case that data cannot be deep-copied,
            # all in-place operations will affect iterable variable.
            # When this DataPipe is iterated second time, it will
            # yield modified items.
            except TypeError:
                warnings.warn(
                    "The input iterable can not be deepcopied, "
                    "please be aware of in-place modification would affect source data."
                )
        for data in source_data:
            yield data

    def __next__(self):
        if self.iter is None:
            self.iter = self.__iter__()
        self.state_counter += 1
        return next(self.iter)

    def save_snapshot(self):
        return self.state_counter

    def restore_snapshot(self, target_count=None):  # This should be called after __setstate__
        if target_count is None:
            target_count = self.state_counter
        self.state_counter = 0
        while self.state_counter < target_count:
            next(self)

    def __getstate__(self):
        # TODO: If iter is not None (you started iterating), this DP is not serializable
        #       __getstate__ should be called before iter starts, but save_snapshot can be called anytime
        if self.iter is not None:
            raise Exception("")
        # TODO: Need to materialize the iterable (if it is generator/something that is not serializable)
        #       Otherwise we can just serialize as usual
        #       Do a `try ... except ...`
        #       Materialization can also fail if the elements inside aren't serializable (e.g. file handler)
        # TODO: Add to inline documentation that DataLoader always materialize iterable objects FOR ANY DP THAT USE
        #       POOR MAN's , such as IterableWrapper
        state = self.__dict__.copy()
        del state['iter']
        return state

    def __setstate__(self, state):
        self.__dict__ = state
        self.iter = self.__iter__()

    def __len__(self):
        return len(self.iterable)
