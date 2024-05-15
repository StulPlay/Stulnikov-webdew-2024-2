from flask import Flask, render_template, request, make_response

app = Flask(__name__)


@app.route('/')
def index():
    url = request.url
    return render_template('index.html', url=url)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/args')
def args():
    return render_template('args.html')


@app.route('/headers')
def headers():
    return render_template('headers.html')


@app.route('/cookies')
def cookies():
    response = make_response(render_template('cookies.html'))
    if "User" not in request.cookies:
        response.set_cookie("User", "Mario")
    else:
        response.delete_cookie("User")
    return response


@app.route("/form", methods=["POST", "GET"])
def form():
    return render_template("forms.html")


@app.route("/calc", methods=["POST", "GET"])
def calc():
    res = 0
    error = ''
    if request.method == "POST":
        try:
            a = float(request.form['a'])
            op = request.form['operation']
            b = float(request.form['b'])
            match op:
                case '+':
                    res = a + b
                case '-':
                    res = a - b
                case '/':
                    res = a / b
                case '*':
                    res = a * b
        except ZeroDivisionError:
            error = 'Деление на 0 невозможно'
        except ValueError:
            error = 'Неверный тип данных'

    return render_template("calc.html", res=res, error=error)

@app.route('/check_phone', methods=['GET', 'POST'])
def check_phone():
    error = None
    formatted_phone = None
    if request.method == 'POST':
        phone = request.form['phone']
        # Удаляем все символы, кроме цифр
        phone_digits = ''.join(filter(str.isdigit, phone))
        # Проверяем длину номера телефона
        if len(phone_digits) < 10 or len(phone_digits) > 11:
            error = 'Недопустимый ввод. Неверное количество цифр.'
        else:
            formatted_phone = format_phone(phone_digits)
    return render_template('phone_form.html', error=error, formatted_phone=formatted_phone)

# Функция для форматирования номера телефона
def format_phone(phone):
    if phone.startswith('7'):
        phone = '8' + phone[1:]
    formatted_phone = f'{phone[:1]}-{phone[1:4]}-{phone[4:7]}-{phone[7:9]}-{phone[9:11]}'
    return formatted_phone


if __name__ == "__main__":
    app.run(debug=True)