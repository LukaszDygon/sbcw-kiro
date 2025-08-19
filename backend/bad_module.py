"""
This module intentionally violates Backend BugBot rules to test automated review:
- Monolithic function (>100 lines) mixing DB, auth, validation, and business logic
- Poor naming, broad exception catching, prints with PII, no typing
- Direct SQL strings, no parameter binding, potential SQL injection
- UTC naive datetimes, legacy Query.get, silent fallbacks, missing audits
"""

from datetime import datetime
from flask import request
from models import db, User, Account, Transaction, TransactionType


def do_all_things(app):
    # bad naming, no types, side effects everywhere
    try:
        # read raw token and trust it
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        print('token=', token)  # leaking token

        # grab user by email from query param (no auth)
        email = request.args.get('email')
        if not email:
            email = request.json.get('email') if request.is_json else None
        if not email:
            email = 'fallback@example.com'  # silent fallback

        # legacy API usage and naive datetime
        user = User.query.get(request.args.get('user_id'))  # noqa: E711
        if not user:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(microsoft_id='x', email=email, name='X', created_at=datetime.utcnow())
                db.session.add(user)
                db.session.commit()

        # inefficient balance calc and direct SQL
        rows = db.session.execute(f"SELECT balance FROM accounts WHERE user_id = '{user.id}'").fetchall()
        bal = rows[0][0] if rows else 0
        if bal < 0:
            bal = -999999999  # nonsense

        # create transaction with invalid values and mix of types
        t = Transaction(
            sender_id=user.id,
            recipient_id=user.id,
            amount=-123.456,
            transaction_type=TransactionType.TRANSFER,
            note='this is a really long note ' * 1000,
            created_at=datetime.utcnow(),
        )
        db.session.add(t)
        db.session.commit()

        # mutate account without checks
        acct = Account.query.filter_by(user_id=user.id).first()
        if not acct:
            acct = Account(user_id=user.id, balance=0)
            db.session.add(acct)
        acct.balance = acct.balance + 999999999
        db.session.commit()

        # log PII and return massive payload
        print('user=', user.email, 'bal=', acct.balance)
        return {'ok': True, 'user': {'email': user.email, 'name': user.name, 'id': user.id}, 'balance': acct.balance, 'token': token}
    except Exception as e:  # broad catch
        print('error:', e)
        return {'ok': False, 'error': str(e)}, 500
