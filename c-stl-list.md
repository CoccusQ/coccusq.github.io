# C语言实现STL：list（双向循环链表）

## 前言

有了之前使用C语言实现`vector`的经验，实现`list`双向循环链表就变得简单了很多，重点不再是使用`void*`类型实现任意类型数据的存储，而是双向循环链表的设计。

PS：`list` 的代码其实早在写好`vector`的当天已经写完，只是等到现在才开始写这篇介绍。

传送门：[C语言实现STL：vector（动态数组）](https://coccusq.github.io/c-stl-vector)

## 代码分析

以下是实现代码：

### 初始化操作

```c
/*listNode结构体*/
struct listNode {
    void* item;
    struct listNode* prev;
    struct listNode* next;
};

/*创建新结点*/
struct listNode* createListNode(void* item, size_t sizeOfType) {
    struct listNode* newNode = (struct listNode*)malloc(sizeof(struct listNode));
    if (newNode == NULL) exit(errno);
    newNode->item = malloc(sizeOfType);
    if (newNode->item == NULL) exit(errno);
    if (item != NULL) memcpy(newNode->item, item, sizeOfType);
    newNode->prev = NULL;
    newNode->next = NULL;
    return newNode;
}

/*list结构体*/
struct list {
    struct listNode* head;
    struct listNode* tail;
    int size;
    size_t sizeOfType;
};

/*构造函数，分配初始内存空间*/
void list_init(struct list* L, size_t sizeOfType) {
    L->sizeOfType = sizeOfType;
    L->head = createListNode(NULL, L->sizeOfType);
    L->tail = createListNode(NULL, L->sizeOfType);
    L->head->next = L->tail;
    L->tail->next = L->head;
    L->head->prev = L->tail;
    L->tail->prev = L->head;
    L->size = 0;
}

```

在初始化时，就先分配头结点和尾结点的内存空间，在之后的插入删除操作中，头结点和尾结点是始终不存放数据的，这样可能导致了内存空间的浪费，但是能简化插入删除操作，不需要特别判断在头尾插入删除的操作。

### 插入元素

```c
/*在头部插入元素*/
void list_push_front(struct list* L, void* item) {
    struct listNode* newNode = createListNode(item, L->sizeOfType);
    L->head->next->prev = newNode;
    newNode->next = L->head->next;
    newNode->prev = L->head;
    L->head->next = newNode;
    L->size++;
}

/*在尾部插入元素*/
void list_push_back(struct list* L, void* item) {
    struct listNode* newNode = createListNode(item, L->sizeOfType);
    L->tail->prev->next = newNode;
    newNode->next = L->tail;
    newNode->prev = L->tail->prev;
    L->tail->prev = newNode;
    L->size++;
}

/*在给定位置插入元素*/
void list_insert(struct list* L, void* item, int index) {
    if (index < 0 || index > L->size) return;
    if (index == 0) {
        list_push_front(L, item);
    }
    else if (index == L->size) {
        list_push_back(L, item);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        struct listNode* newNode = createListNode(item, L->sizeOfType);
        p->next->prev = newNode;
        newNode->next = p->next;
        newNode->prev = p;
        p->next = newNode;
        L->size++;
    }
    else {
        struct listNode* p = L->tail;
        for (int i = L->size - 1; i > index - 1; i--) {
            p = p->prev;
        }
        struct listNode* newNode = createListNode(item, L->sizeOfType);
        p->prev->next = newNode;
        newNode->prev = p->prev;
        newNode->next = p;
        p->prev = newNode;
        L->size++;
    }
}
```

### 删除元素

```c
/*删除头部元素*/
void list_pop_front(struct list* L) {
    struct listNode* toDelete = L->head->next;
    L->head->next = toDelete->next;
    toDelete->next->prev = L->head;
    free(toDelete->item);
    free(toDelete);
    L->size--;
}

/*删除尾部元素*/
void list_pop_back(struct list* L) {
    struct listNode* toDelete = L->tail->prev;
    L->tail->prev = toDelete->prev;
    toDelete->prev->next = L->tail;
    free(toDelete->item);
    free(toDelete);
    L->size--;
}

/*删除给定位置的元素*/
void list_erase(struct list* L, int index) {
    if (index < 0 || index >= L->size) return;
    if (index == 0) {
        list_pop_front(L);
    }
    else if (index == L->size - 1) {
        list_pop_back(L);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        struct listNode* toDelete = p->next;
        p->next = toDelete->next;
        toDelete->next->prev = p;
        free(toDelete->item);
        free(toDelete);
        L->size--;
    }
    else {
        struct listNode* p = L->tail;
        for (int i = L->size - 1; i > index; i--) {
            p = p->prev;
        }
        struct listNode* toDelete = p->prev;
        p->prev = toDelete->prev;
        toDelete->prev->next = p;
        free(toDelete->item);
        free(toDelete);
        L->size--;
    }
}
```

### 实现元素随机访问

```c
/*访问头部元素*/
void* list_front(struct list* L) {
    return L->head->next->item;
}

/*访问尾部元素*/
void* list_back(struct list* L) {
    return L->tail->prev->item;
}

/*随机访问元素*/
void* list_get(struct list* L, int index) {
    if (index < 0 || index > L->size - 1) return NULL;
    if (index == 0) {
        return list_front(L);
    }
    else if (index == L->size - 1) {
        return list_back(L);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head->next;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        return p->item;
    }
    else {
        struct listNode* p = L->tail->prev;
        for (int i = L->size - 1; i > index; i--) {
            p = p->prev;
        }
        return p->item;
    }
}
```

在随机访问元素时，根据索引的位置决定是从头部开始遍历还是从尾部开始遍历，能够在一定程度上减少遍历的时间。

### 清零和析构操作

```c
/*清空链表*/
void list_clear(struct list* L) {
    struct listNode* p = L->head->next;
    while (p != L->tail) {
        struct listNode* toDelete = p;
        p = p->next;
        free(toDelete->item);
        free(toDelete);
    }
    L->tail->prev = L->head;
    L->size = 0;
}

/*析构函数，释放动态分配的内存*/
void list_free(struct list* L) {
    struct listNode* p = L->head->next;
    while (p != L->tail) {
        struct listNode* toDelete = p;
        p = p->next;
        free(toDelete->item);
        free(toDelete);
    }
    free(L->head);
    free(L->tail);
}
```

### 一些宏定义

```c
/*简化构造函数的调用*/
#define LIST(type, name) struct list name; list_init(&name, sizeof(type))

#define LIST_GET(type, name, index) *(type*)list_get(&name, index)

#define LIST_FRONT(type, name) *(type*)list_front(&name)

#define LIST_BACK(type, name) *(type*)list_back(&name)
```

和之前的`vector`一样，利用宏的替换机制，实现类似于C++模板的编译时替换操作；同时将动态数组的随机访问函数的返回值进行操作，将原来的`void*`类型依据数据类型转换成数值，便于进行赋值操作。

## 小结一下

这是C语言实现STL系列的第二个成果，其中的关键技术，也就是实现不同类型数据的存储部分，已经在`vector`中大致搞清楚了，所以这次的`list`只是为了完善C语言实现STL的附加产物，这次的主要部分在于双向循环链表的设计与实现。

最后是完整的头文件代码：

### 完整代码

```c
#ifndef _LIST_H_
#define _LIST_H_
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#define LIST(type, name) struct list name; list_init(&name, sizeof(type))
#define LIST_GET(type, name, index) *(type*)list_get(&name, index)
#define LIST_FRONT(type, name) *(type*)list_front(&name)
#define LIST_BACK(type, name) *(type*)list_back(&name)

struct listNode {
    void* item;
    struct listNode* prev;
    struct listNode* next;
};

struct listNode* createListNode(void* item, size_t sizeOfType) {
    struct listNode* newNode = (struct listNode*)malloc(sizeof(struct listNode));
    if (newNode == NULL) exit(errno);
    newNode->item = malloc(sizeOfType);
    if (newNode->item == NULL) exit(errno);
    if (item != NULL) memcpy(newNode->item, item, sizeOfType);
    newNode->prev = NULL;
    newNode->next = NULL;
    return newNode;
}

struct list {
    struct listNode* head;
    struct listNode* tail;
    int size;
    size_t sizeOfType;
};

void list_init(struct list* L, size_t sizeOfType) {
    L->sizeOfType = sizeOfType;
    L->head = createListNode(NULL, L->sizeOfType);
    L->tail = createListNode(NULL, L->sizeOfType);
    L->head->next = L->tail;
    L->tail->next = L->head;
    L->head->prev = L->tail;
    L->tail->prev = L->head;
    L->size = 0;
}

void list_push_front(struct list* L, void* item) {
    struct listNode* newNode = createListNode(item, L->sizeOfType);
    L->head->next->prev = newNode;
    newNode->next = L->head->next;
    newNode->prev = L->head;
    L->head->next = newNode;
    L->size++;
}

void list_push_back(struct list* L, void* item) {
    struct listNode* newNode = createListNode(item, L->sizeOfType);
    L->tail->prev->next = newNode;
    newNode->next = L->tail;
    newNode->prev = L->tail->prev;
    L->tail->prev = newNode;
    L->size++;
}

void list_pop_front(struct list* L) {
    struct listNode* toDelete = L->head->next;
    L->head->next = toDelete->next;
    toDelete->next->prev = L->head;
    free(toDelete->item);
    free(toDelete);
    L->size--;
}

void list_pop_back(struct list* L) {
    struct listNode* toDelete = L->tail->prev;
    L->tail->prev = toDelete->prev;
    toDelete->prev->next = L->tail;
    free(toDelete->item);
    free(toDelete);
    L->size--;
}

void list_insert(struct list* L, void* item, int index) {
    if (index < 0 || index > L->size) return;
    if (index == 0) {
        list_push_front(L, item);
    }
    else if (index == L->size) {
        list_push_back(L, item);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        struct listNode* newNode = createListNode(item, L->sizeOfType);
        p->next->prev = newNode;
        newNode->next = p->next;
        newNode->prev = p;
        p->next = newNode;
        L->size++;
    }
    else {
        struct listNode* p = L->tail;
        for (int i = L->size - 1; i > index - 1; i--) {
            p = p->prev;
        }
        struct listNode* newNode = createListNode(item, L->sizeOfType);
        p->prev->next = newNode;
        newNode->prev = p->prev;
        newNode->next = p;
        p->prev = newNode;
        L->size++;
    }
}

void list_erase(struct list* L, int index) {
    if (index < 0 || index >= L->size) return;
    if (index == 0) {
        list_pop_front(L);
    }
    else if (index == L->size - 1) {
        list_pop_back(L);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        struct listNode* toDelete = p->next;
        p->next = toDelete->next;
        toDelete->next->prev = p;
        free(toDelete->item);
        free(toDelete);
        L->size--;
    }
    else {
        struct listNode* p = L->tail;
        for (int i = L->size - 1; i > index; i--) {
            p = p->prev;
        }
        struct listNode* toDelete = p->prev;
        p->prev = toDelete->prev;
        toDelete->prev->next = p;
        free(toDelete->item);
        free(toDelete);
        L->size--;
    }
}

void* list_front(struct list* L) {
    return L->head->next->item;
}

void* list_back(struct list* L) {
    return L->tail->prev->item;
}

void* list_get(struct list* L, int index) {
    if (index < 0 || index > L->size - 1) return NULL;
    if (index == 0) {
        return list_front(L);
    }
    else if (index == L->size - 1) {
        return list_back(L);
    }
    else if (index <= L->size / 2) {
        struct listNode* p = L->head->next;
        for (int i = 0; i < index; i++) {
            p = p->next;
        }
        return p->item;
    }
    else {
        struct listNode* p = L->tail->prev;
        for (int i = L->size - 1; i > index; i--) {
            p = p->prev;
        }
        return p->item;
    }
}

void list_clear(struct list* L) {
    struct listNode* p = L->head->next;
    while (p != L->tail) {
        struct listNode* toDelete = p;
        p = p->next;
        free(toDelete->item);
        free(toDelete);
    }
    L->tail->prev = L->head;
    L->size = 0;
}

void list_free(struct list* L) {
    struct listNode* p = L->head->next;
    while (p != L->tail) {
        struct listNode* toDelete = p;
        p = p->next;
        free(toDelete->item);
        free(toDelete);
    }
    free(L->head);
    free(L->tail);
}

#endif
```