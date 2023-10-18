from local import APP

if app == 'mlc':
    from mlc import app as application
elif app == 'ucla':
    from ucla import app as application
