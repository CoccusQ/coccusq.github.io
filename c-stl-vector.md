# C语言实现STL：vector（动态数组）

#### By [CoccusQ](https://github.com/CoccusQ) 2024.10.31

- [前言](#前言)
- [正片开始：代码分析](#代码分析)
- [小结一下](#小结一下)
- [补充：完整代码](#完整代码)

### 前言

C语言实现动态数组的原理并不复杂，只需要实现数组元素的插入和删除、随机访问以及根据当前数组内元素数量自动调整数组占用内存大小的功能即可。

唯一的难点在于存储不同类型的数据。C++ STL中的`vector`利用了C++的模板功能，能够存储任意类型数据，而想要在C语言中实现类似的功能，就需要利用到`void*`指针。`void*`指针只存储一个地址，而不关心这个地址内存储的数据类型，因此我们只需要按照不同数据类型的字节数来访问`void*`中的数据。

例如，如果我们要动态分配一块内存给一个`int`数组，常规做法就是使用`stdlib.h`中的`malloc`函数，代码如下：

```c
int num = 24;
int* array = (int*)malloc(sizeof(int) * num);
```

事实上，无论`malloc`还是`calloc`、`realloc`，这些函数返回的内存地址都是以`void*`指针作为载体的，而内存的分配过程也是“简单粗暴”地将`int`的字节数乘上数组的元素个数，而程序员在访问内存的时候只要以`int`的字节数为单位进行，数据就不会出错。

### 代码分析

以下是实现代码：

1. 初始化操作

```c
/*vector结构体*/
struct vector {
    int capacity;
    int size;
    void* items;
    size_t sizeOfType;
};

/*构造函数，分配初始内存空间*/
void vector_init(struct vector* v, int capacity, size_t sizeOfType) {
    v->capacity = capacity;
    v->sizeOfType = sizeOfType;
    v->size = 0;
    v->items = calloc(v->capacity, v->sizeOfType);
    if (v->items == NULL) exit(errno);
}

/*重新调整数组大小，且原来的元素不会丢失*/
void vector_resize(struct vector* v, int capacity) {
    void* temp = v->items;
    int temp_cap = v->capacity;
    v->capacity = capacity;
    v->items = realloc(v->items, v->sizeOfType * v->capacity);
    if (v->items == NULL) exit(errno);
    if (v->items != temp)
        memmove(v->items, temp, v->sizeOfType * temp_cap);
}
```

其中，`vector`类（其实是结构体）的数据成员有容量`capacity`、元素个数`size`、指向数组首地址的指针`item`、当前数组内存放数据的字节数`sizeOfType`，`vector_init`函数和`vector_resize`函数的内存分配过程均是以`sizeOfType`为单位进行。

细节：

- 在复制整个数组时，采用`memmove`而不是`memcpy`，因为在重新分配内存时新的内存空间可能和旧的空间有重合，这种重合的情况在`memcpy`是未定义行为，而`memmove`会在遇到重合的时候创建一个临时缓冲区进行复制，更安全。

- `calloc`和`realloc`：与`malloc`不同，`calloc`在分配内存时还会把每个元素初始化为0；而`realloc`会尝试在原来的地址处调整内存空间大小，如果空间足够，原来的数据就不会丢失，只有空间不够的情况下才会重新找一块内存，这时候原来的数据就不能一起迁移过来，需要重新复制一遍，`vector_resize`函数的最后两行就是在做这个判断（如果新分配的指针地址和原来不一样，说明起始地址变了，需要  复制原来的数据到新的内存空间里）。

2. 插入元素

```c
/*在尾部插入元素*/
void vector_push_back(struct vector* v, void* item) {
    if (v->size >= v->capacity)
        vector_resize(v, v->capacity * 2);
    memcpy(v->items + (v->size * v->sizeOfType), item, v->sizeOfType);
    v->size++;
}

/*在给定位置插入元素*/
void vector_insert(struct vector* v, void* item, int index) {
    if (index < 0) return;
    if (index >= v->size) {
        vector_push_back(v, item);
    }
    else {
        if (v->size >= v->capacity)
            vector_resize(v, v->capacity * 2);
        memmove(v->items + (index + 1) * v->sizeOfType, v->items + index * v->sizeOfType, v->sizeOfType * (v->size - index));
        v->size++;
        memcpy(v->items + (index * v->sizeOfType), item, v->sizeOfType);
    }
}
```

3. 删除元素

```c
/*删除尾部元素*/
void vector_pop_back(struct vector* v) {
    if (v->size <= 0) return;
    v->size--;
    if (v->size < v->capacity / 3) 
        vector_resize(v, v->capacity / 2);
}

/*删除给定位置的元素*/
void vector_erase(struct vector* v, int index) {
    if (index < 0 || index >= v->size) return;
    if (index == v->size - 1) {
        vector_pop_back(v);
    }
    else {
        memmove(v->items + index * v->sizeOfType, v->items + (index + 1) * v->sizeOfType, v->sizeOfType * (v->size - index - 1));
        v->size--;
        if (v->size < v->capacity / 3)
            vector_resize(v, v->capacity / 3);
    }
}
```

4. 实现元素随机访问（ps: 随机访问和随机数没关系，是能不按顺序直接访问任意一个元素的意思）

```c
/*访问头部元素*/
void* vector_front(struct vector* v) {
    return v->items;
}

/*访问尾部元素*/
void* vector_back(struct vector* v) {
    if (v->size < 1) return NULL;
    return v->items + (v->size - 1) * v->sizeOfType;
}

/*随机访问元素*/
void* vector_get(struct vector* v, int index) {
    if (index < 0 || index >= v->size) return NULL;
    return v->items + index * v->sizeOfType;
}
```

访问时的`v->sizeOfType`就是在按照元素类型的字节数访问，保证读取的数据正确。

5. 清零和析构操作

```c
/*清空数组*/
void vector_clear(struct vector* v) {
    if (v->size == 0) return;
    memset(v->items, 0, v->sizeOfType * v->capacity);
}

/*析构函数，释放动态分配的内存*/
void vector_free(struct vector* v) {
    free(v->items);
}
```

6. 一些宏定义

```c
/*简化构造函数的调用*/
#define VECTOR(type, name, capacity) struct vector name; vector_init(&name, capacity, sizeof(type))

#define VECTOR_GET(type, name, index) *(type*)vector_get(&name, index)

#define VECTOR_FRONT(type, name) *(type*)vector_front(&name)

#define VECTOR_BACK(type, name) *(type*)vector_back(&name)
```

利用宏的替换机制，实现类似于C++模板的编译时替换操作；同时将动态数组的随机访问函数的返回值进行操作，将原来的`void*`类型依据数据类型转换成数值，便于进行赋值操作。

（ps：这一部分对c语言宏的使用是我感觉最有意思的地方。）

### 小结一下

这是C语言实现STL系列的第一个尝试，由于语言特点和个人技术，最终的使用效果和性能离STL这种工业级轮子有很大的差距，不过使用C语言的种种特性来完成一些巧妙的操作还是非常有意思的，尤其是利用`void*`类型实现不同类型数据的存储（其实这里的灵感也来源于标准库里的`malloc`函数申请内存的用法）

最后是完整的头文件代码：

#### 完整代码

```c
/*vector.h*/
#ifndef _VECTOR_H_
#define _VECTOR_H_
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#define VECTOR(type, name, capacity) struct vector name; vector_init(&name, capacity, sizeof(type))
#define VECTOR_GET(type, name, index) *(type*)vector_get(&name, index)
#define VECTOR_FRONT(type, name) *(type*)vector_front(&name)
#define VECTOR_BACK(type, name) *(type*)vector_back(&name)

struct vector {
    int capacity;
    int size;
    void* items;
    size_t sizeOfType;
};

void vector_init(struct vector* v, int capacity, size_t sizeOfType) {
    v->capacity = capacity;
    v->sizeOfType = sizeOfType;
    v->size = 0;
    v->items = calloc(v->capacity, v->sizeOfType);
    if (v->items == NULL) exit(errno);
}

void vector_resize(struct vector* v, int capacity) {
    void* temp = v->items;
    int temp_cap = v->capacity;
    v->capacity = capacity;
    v->items = realloc(v->items, v->sizeOfType * v->capacity);
    if (v->items == NULL) exit(errno);
    if (v->items != temp)
        memmove(v->items, temp, v->sizeOfType * temp_cap);
}

void vector_push_back(struct vector* v, void* item) {
    if (v->size >= v->capacity)
        vector_resize(v, v->capacity * 2);
    memcpy(v->items + (v->size * v->sizeOfType), item, v->sizeOfType);
    v->size++;
}

void vector_pop_back(struct vector* v) {
    if (v->size <= 0) return;
    v->size--;
    if (v->size < v->capacity / 3) 
        vector_resize(v, v->capacity / 2);
}

void vector_insert(struct vector* v, void* item, int index) {
    if (index < 0) return;
    if (index >= v->size) {
        vector_push_back(v, item);
    }
    else {
        if (v->size >= v->capacity)
            vector_resize(v, v->capacity * 2);
        memmove(v->items + (index + 1) * v->sizeOfType, v->items + index * v->sizeOfType, v->sizeOfType * (v->size - index));
        v->size++;
        memcpy(v->items + (index * v->sizeOfType), item, v->sizeOfType);
    }
}

void vector_erase(struct vector* v, int index) {
    if (index < 0 || index >= v->size) return;
    if (index == v->size - 1) {
        vector_pop_back(v);
    }
    else {
        memmove(v->items + index * v->sizeOfType, v->items + (index + 1) * v->sizeOfType, v->sizeOfType * (v->size - index - 1));
        v->size--;
        if (v->size < v->capacity / 3)
            vector_resize(v, v->capacity / 3);
    }
}

void* vector_front(struct vector* v) {
    return v->items;
}

void* vector_back(struct vector* v) {
    if (v->size < 1) return NULL;
    return v->items + (v->size - 1) * v->sizeOfType;
}

void* vector_get(struct vector* v, int index) {
    if (index < 0 || index >= v->size) return NULL;
    return v->items + index * v->sizeOfType;
}

void vector_clear(struct vector* v) {
    if (v->size == 0) return;
    memset(v->items, 0, v->sizeOfType * v->capacity);
}

void vector_free(struct vector* v) {
    free(v->items);
}
#endif
```