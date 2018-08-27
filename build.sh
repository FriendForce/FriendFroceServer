#!/bin/bash
cd $REACT_APP
npm run build
cd -
cp -r $REACT_APP/build $SERVER_ROOT/app/react_app
cp -r $REACT_APP/build/static/* $SERVER_ROOT/app/static/
