from PIL import Image


def image_resize(filename):
    file_split = filename.split('.')
    image = Image.open('app/static/img/{}'.format(filename))
    image.thumbnail((600, 400))
    image.save('app/static/img/{}-small.{}'.format(file_split[0], file_split[1]))
    image.save('app/static/img/{}-small.webp'.format(file_split[0]))
    print("OK")


if __name__ == "__main__":
    image_resize('test.jpg')