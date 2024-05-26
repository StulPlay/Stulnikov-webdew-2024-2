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
    error_message = None
    formatted_phone = None
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')

        # Проверяем на наличия запрещенных символов
        pars_err = False
        allowed_chars = '0123456789()+-. '
        for char in phone_number:
            if char not in allowed_chars:
                pars_err = True
                break

        # Удаляем все символы, кроме цифр
        phone_digits = ''.join(filter(str.isdigit, phone_number))


        # Проверяем длину номера телефона
        if len(phone_digits) < 10 or len(phone_digits) > 11:
            error_message = 'Недопустимый ввод. Неверное количество цифр.'
        elif pars_err:
            error_message = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
        else:
            # Берем последние 10 цифр для обработки нужных цифр
            digits = phone_digits[-10:]
            # Преобразуем номер к формату 8-***-***-**-**
            formatted_phone = '8-{}-{}-{}-{}'.format(digits[:3], digits[3:6], digits[6:8], digits[8:])
    return render_template('phone_form.html', error_message=error_message, formatted_phone=formatted_phone)

if __name__ == "__main__":
    app.run(debug=True)