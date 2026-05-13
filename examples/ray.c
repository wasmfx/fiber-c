#include "math.h"

#define min(x, y) ( (x) < (y) ? (x) : (y) )
#define max(x, y) ( (x) >= (y) ? (x) : (y) )

#define WIDTH 600
#define HEIGHT 600
static char BUFFER[4 * HEIGHT * WIDTH] = {0};

#define export(NAME) __attribute__((export_name(NAME)))

struct pt {
    float x, y, z;
};

const struct pt viewpoint =  {0, 3, 0};
const struct pt cameraAngle =  {0, 0, 1};
const struct pt planenormal =  {0, 1, 0};

const struct pt sphereCenter =  {-1, 1, 70};
const float sphereRadius = 1;

const struct pt lightSource = {10, 20, 0};

float
dot(const struct pt *a, const struct pt *b)
{
    return a->x * b->x + a->y * b->y + a->z * b->z;
}

void
scaleOut(const struct pt *a, float n, const struct pt *v, struct pt *result)
{
    result->x = a->x + n * v->x;
    result->y = a->y + n * v->y;
    result->z = a->z + n * v->z;
}

void
normalize(struct pt *v)
{
    float size = sqrt(dot(v, v));
    v->x = v->x / size;
    v->y = v->y / size;
    v->z = v->z / size;
}

int
planeHit(const struct pt *viewpoint, const struct pt *viewdir, const struct pt *planenormal, struct pt *result)
{
    float n = -dot(viewpoint, planenormal) / dot(viewdir, planenormal);
    if (n > 0) {
        result->x = viewpoint->x + n * viewdir->x;
        result->y = viewpoint->y + n * viewdir->y;
        result->z = viewpoint->z + n * viewdir->z;
        return 1;
    } else {
        result->x = 0;
        result->y = 0;
        result->z = 0;
        return 0;
    }
}

void
diff(const struct pt *a, const struct pt *b, struct pt *result)
{
    result->x = a->x - b->x;
    result->y = a->y - b->y;
    result->z = a->z - b->z;
}

int
sphereHit(const struct pt *viewpoint, const struct pt *viewdir, const struct pt *sphereCenter, float radius, struct pt *result) {
    float a = dot(viewdir, viewdir);
    float b = 2 * dot(viewpoint, viewdir) - 2 * dot(viewdir, sphereCenter);
    float c = dot(viewpoint, viewpoint) + dot(sphereCenter, sphereCenter) - 2 * dot(viewpoint, sphereCenter) - radius * radius;
    float discrim = b * b - 4 * a * c;
    if (discrim < 0) return 0;
    float npos = (-b + sqrt(b * b - 4 * a * c)) / 2 * a;
    float nneg = (-b - sqrt(b * b - 4 * a * c)) / 2 * a;
    if (nneg <= 0 && npos <= 0) return 0;
    float n;
    if (nneg < 0) {
        n = npos;
    }
    if (npos < 0) {
        n = nneg;
    }
    if (nneg > 0 && npos > 0) {
        n = min(nneg, npos);
    };
    scaleOut(viewpoint, n, viewdir, result);
    return 1;
}

void
setPixel(char *buffer, int width, int i, int j, char alpha, char blue, char green, char red)
{
    // I don't know why the -264 offset is needed :-/
    // buffer[4 * (i*width + j - 264) + 0] = alpha;
    // buffer[4 * (i*width + j - 264) + 1] = blue;
    // buffer[4 * (i*width + j - 264) + 2] = green;
    // buffer[4 * (i*width + j - 264) + 3] = red;
    buffer[4 * (i*width + j - 264) + 0] = red;
    buffer[4 * (i*width + j - 264) + 1] = green;
    buffer[4 * (i*width + j - 264) + 2] = blue;
    buffer[4 * (i*width + j - 264) + 3] = alpha;
}

export("getBuffer")
char *
getBuffer() {
    return BUFFER;
}

export("render")
int
render() {
    for (int i = 0; i < HEIGHT; i++){
        for (int j = 0; j < WIDTH; j++){
            // if (((i/4 + j/4) % 2)) {
            //     BUFFER[4 * (i*WIDTH + j) + 0] = 0xFF;
            //     BUFFER[4 * (i*WIDTH + j) + 1] = 0xA0;
            //     BUFFER[4 * (i*WIDTH + j) + 2] = 0x00;
            //     BUFFER[4 * (i*WIDTH + j) + 3] = 0x00;
            // } else {
            //     BUFFER[4 * (i*WIDTH + j) + 0] = 0xFF;
            //     BUFFER[4 * (i*WIDTH + j) + 1] = 0x20;
            //     BUFFER[4 * (i*WIDTH + j) + 2] = 0xC0;
            //     BUFFER[4 * (i*WIDTH + j) + 3] = 0xC0;
            // }

            struct pt ray = {
                // Note: distorted, not normalized.
                ((float)j/WIDTH - 0.5) * 0.2,
                -((float)i/HEIGHT - 0.5) * 0.2,
                1,
            };

            struct pt hitPt;

            if (sphereHit(&viewpoint, &ray, &sphereCenter, sphereRadius, &hitPt)) {
                struct pt sphereVector;
                struct pt lightVector;
                diff(&hitPt, &sphereCenter, &sphereVector);
                normalize(&sphereVector);
                diff(&lightSource, &sphereCenter, &lightVector);
                normalize(&lightVector);
                float incidence = dot(&sphereVector, &lightVector);
                incidence = max(incidence, 0);
                setPixel(BUFFER, WIDTH, i, j, 0xFF, 0xFF * incidence, 0x00, 0x7F * incidence + 0x80);
                continue;
            }
            if (planeHit(&viewpoint, &ray, &planenormal, &hitPt)) {
                char value;
                if (((int)(hitPt.x / 1.0) + (int)(hitPt.z / 1.0)) % 2) {
                    value = 0xFF;
                } else {
                    value = 0x00;
                }
                setPixel(BUFFER, WIDTH, i, j, 0xFF, value, value, 0xFF);
            } else {
                setPixel(BUFFER, WIDTH, i, j, 0xFF, 0x00, 0xA0, 0xFF);
            }
        }
    }
    return 747;
}