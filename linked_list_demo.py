# 链表节点类
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

# 链表类
class LinkedList:
    def __init__(self):
        self.head = None
    
    def append(self, value):
        new_node = Node(value)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node
    
    def traverse(self):
        nodes = []
        current = self.head
        while current:
            nodes.append(current.value)
            current = current.next
        return nodes
    
    def delete_at(self, index):
        if not self.head:
            return False
        
        if index == 0:
            self.head = self.head.next
            return True
        
        current = self.head
        for i in range(index - 1):
            if current.next is None:
                return False
            current = current.next
        
        if current.next is None:
            return False
        
        current.next = current.next.next
        return True

# 创建链表并添加节点 4, 6, 8, 0
ll = LinkedList()
for value in [4, 6, 8, 0]:
    ll.append(value)

print("原始链表:", ll.traverse())

# 删除索引为2的节点
ll.delete_at(2)

print("删除索引2后的链表:", ll.traverse())
