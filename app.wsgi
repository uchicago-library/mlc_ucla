from local import APP

if APP == 'mlc':
    from mlc import app as application
elif APP == 'ucla':
    from ucla import app as application
