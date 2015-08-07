# -*- coding: utf-8 -*-

"""
Forked from: https://www.kaggle.com/karma86/grasp-and-lift-eeg-detection/rf-lda-lr-v2-1/run/41141
@author Ajoo
forked from Adam Gągol's script based on Elena Cuoco's

"""

import numpy as np
import pandas as pd
from scipy.signal import butter, lfilter
from sklearn.linear_model import LogisticRegression
from sklearn.lda import LDA
from sklearn.qda import QDA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn import svm
#############function to read data###########
FNAME = "/media/winter/DA70C3D670C3B791/eegdata/data/input/{0}/subj{1}_series{2}_{3}.csv"
def load_data(subj, series=range(1,9), prefix = 'train'):
    data = [pd.read_csv(FNAME.format(prefix,subject,s,'data'), index_col=0) for s in series]
    idx = [d.index for d in data]
    data = [d.values.astype(float) for d in data]
    if prefix == 'train':
        events = [pd.read_csv(FNAME.format(prefix,subject,s,'events'), index_col=0).values for s in series]
        return data, events
    else:
        return data, idx

def compute_features(X, scale=None):
    X0 = [x[:,0] for x in X]
    X = np.concatenate(X, axis=0)
    F = [];
    for fc in np.linspace(0,1,11)[1:]:
        b,a = butter(3,fc/250.0,btype='lowpass')
        F.append(np.concatenate([lfilter(b,a,x0) for x0 in X0], axis=0)[:,np.newaxis])
    F = np.concatenate(F, axis=1)
    F = np.concatenate((X,F,F**2), axis=1)
        
    if scale is None:    
        scale = StandardScaler()
        F = scale.fit_transform(F)
        return F, scale
    else:
        F = scale.transform(F)
        return F


#%%########### Initialize ####################################################
cols = ['HandStart','FirstDigitTouch',
        'BothStartLoadPhase','LiftOff',
        'Replace','BothReleased']

subjects = range(1,13)
idx_tot = []
scores_tot = []
scores_tot2 = []

###loop on subjects and 8 series for train data + 2 series for test data
for subject in subjects:

    X_train, y = load_data(subject)
    X_test, idx = load_data(subject,[9,10],'test')

################ Train classifiers ###########################################
    lda = LDA()
    rf = RandomForestClassifier(n_estimators=200, n_jobs=-1, criterion="entropy", random_state=1)
    lr = LogisticRegression()
    #svm = svm.SVC(probability=True)
    clf = svm.SVC(probability=True)
    
    X_train, scaler = compute_features(X_train)
    X_test = compute_features(X_test, scaler)   #pass the learned mean and std to normalized test data
    
    y = np.concatenate(y,axis=0)
    scores = np.empty((X_test.shape[0],6))
    scores2 = np.empty((X_test.shape[0],6))
    
    downsample = 40
    # test SVM for 2 first subjects
    if subject in [2,4]:
        for i in range(6):
            print('Train subject %d, class %s' % (subject, cols[i]))
            rf.fit(X_train[::downsample,:], y[::downsample,i])
            lda.fit(X_train[::downsample,:], y[::downsample,i])
            lr.fit(X_train[::downsample,:], y[::downsample,i])
            clf.fit(X_train[::downsample,:], y[::downsample,i])  
           
            scores[:,i] = (rf.predict_proba(X_test)[:,1]*0.10 + 
                            lda.predict_proba(X_test)[:,1]*0.40 + 
                            lr.predict_proba(X_test)[:,1]*0.20 +
                            clf.predict_proba(X_test)[:,1]*0.30)
            scores2[:,i] = (rf.predict_proba(X_test)[:,1]*0.10 + 
                            lda.predict_proba(X_test)[:,1]*0.4 + 
                            lr.predict_proba(X_test)[:,1]*0.15 +
                            clf.predict_proba(X_test)[:,1]*0.35)
            scores2[:,i] = scores[:,i]

    scores_tot.append(scores)
    scores_tot2.append(scores2)
    idx_tot.append(np.concatenate(idx))
    
#%%########### submission file ################################################
submission_file = 'svm_ensemble4_test3.csv'
# create pandas object for submission
submission = pd.DataFrame(index=np.concatenate(idx_tot),
                          columns=cols,
                          data=np.concatenate(scores_tot))

# write file
submission.to_csv(submission_file,index_label='id',float_format='%.3f')

# Second file:
submission_file = 'svm_ensemble_test4.csv'
# create pandas object for submission
submission = pd.DataFrame(index=np.concatenate(idx_tot),
                          columns=cols,
                          data=np.concatenate(scores_tot2))

# write file
submission.to_csv(submission_file,index_label='id',float_format='%.3f')