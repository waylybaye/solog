from haystack import indexes
from blog.models import Post
from blog.utils import segment


#class PostIndex(indexes.RealTimeSearchIndex, indexes.Indexable):
#    title = indexes.CharField(model_attr='title')
#    author = indexes.CharField(model_attr='user')
#    content_auto = indexes.NgramField(model_attr='content')
#    text = indexes.CharField(document=True)
#
#    def get_model(self):
#        return Post
#
#    def __init__(self):
#        super(PostIndex, self).__init__()
#
#    def prepare_title(self, object):
#        return segment(object.title)
#
#    def prepare_author(self, object):
#        return segment(object.user.get_full_name() + ' ' + object.user.username)
#
#    def prepare_content_auto(self, object):
#        return segment(object.content)
#
#    def prepare(self, object):
#        print "index", object, "..."
#        self.prepared_data = super(PostIndex, self).prepare(object)
#        self.prepared_data['text'] = self.prepared_data['title'] + ' ' + self.prepared_data['author'] +  ' ' + self.prepared_data['content_auto']
#        return self.prepared_data
