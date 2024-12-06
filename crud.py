def add(name, id):
    list = [id]
    if id in list:
        print("Succesfully added!")
    else:
        print("Not added")

def view():
    for x in list:
        print(x, "ID: ", list[x] )

name = input("Enter your name: ")
id = int(input("Enter your id: "))

add(name, id)
view()