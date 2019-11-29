class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def sit(self):
        return (f'{self.name} sit')


    def roll_over(self):
        return (f'{self.name} roll over')


class Mache_dog(Dog):
    def __init__(self, name, age):
        super().__init__(name, age)
    def roll_over(self):
        return ('mache_dog can not roll over')


dog = Dog('qiao ba','20')
print(dog.roll_over())

mache_dog = Mache_dog('qiao ba2', '21')
print(mache_dog.roll_over())
