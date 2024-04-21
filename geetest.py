
def get_validate(gt, challenge):
    print(gt, challenge)
    validate = input(f"validate: ")
    seccode = f"{validate}|jordan"
    return (seccode, validate)
