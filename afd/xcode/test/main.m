
    #import <Foundation/Foundation.h>
    #import <objc/runtime.h>

    int main(void) {
        Class c = NSClassFromString(@"User(UserPrivate)");
        void* p = method_getImplementation(class_getClassMethod(c, @selector(_findUserName:searchParent:)));
        if (p == NULL) {
            void* p = method_getImplementation(class_getInstanceMethod(c, @selector(_findUserName:searchParent:)));
            NSLog(@"POINTER:%p", p);
        }
        else {
            NSLog(@"POINTER:%p", p);
        }
        // NSLog(@"%@", [c performSelector: @selector(_findUserName:searchParent:)]);
    }
        