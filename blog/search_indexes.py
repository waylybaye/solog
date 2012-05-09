from haystack import indexes
from blog.models import Post

class PostIndex(indexes.SearchIndex, indexes.Indexable):
    title = indexes.CharField(model_attr='title')
    author = indexes.CharField(model_attr='user')
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Post

