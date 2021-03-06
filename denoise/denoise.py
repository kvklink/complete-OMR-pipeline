import cv2 as cv

'''Denoises an image. The output color scheme matches input (gray or RGB).'''


def denoise(img, is_rgb=False):
    if is_rgb:
        img = cv.cvtColor(img, cv.COLOR_RGB2GRAY)

    cv.normalize(img, img, 0, 165, cv.NORM_MINMAX)
    _, img = cv.threshold(img, 0, 255, cv.THRESH_OTSU)
    img = cv.fastNlMeansDenoising(img, None, 20, 7, 21)

    if is_rgb:
        img = cv.cvtColor(img, cv.COLOR_GRAY2RGB)
    return img


def denoise_at(path, is_rgb=False):
    return denoise(cv.imread(path, cv.IMREAD_GRAYSCALE), is_rgb)


if __name__ == "__main__":
    cv.imshow('output', denoise_at('../images/sheets/mscd-15/input.png'))
    cv.waitKey(0)
    cv.destroyAllWindows()
    cv.waitKey(1)
