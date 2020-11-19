class Client(object):

    def __init__(self, **kwargs):
        self.name = None
        self.points = 0
        self.last_message = None
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '{"name": "'+str(self.name)+'", "points": '+str(self.points)+', "last_message": "'+str(self.last_message)+'"}'

