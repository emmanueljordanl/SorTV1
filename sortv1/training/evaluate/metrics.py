import numpy as np

def metrics(truth, predicted, probabilities=None, *, top1=0.80, margin=0.15):
    truth=np.asarray(truth,dtype=int); predicted=np.asarray(predicted,dtype=int)
    if truth.shape!=predicted.shape or len(truth)==0 or ((truth<0)|(truth>3)|(predicted<0)|(predicted>3)).any(): raise ValueError("Invalid evaluation labels")
    confusion=np.zeros((4,4),dtype=int)
    for actual, inferred in zip(truth,predicted): confusion[actual,inferred]+=1
    precision=[]; recall=[]; f1=[]
    for i in range(4):
        tp=int(confusion[i,i]); n_actual=int(confusion[i].sum()); n_pred=int(confusion[:,i].sum())
        pr=tp/n_pred if n_pred else None; re=tp/n_actual if n_actual else None
        precision.append(pr); recall.append(re); f1.append(2*tp/(n_actual+n_pred) if n_actual+n_pred else 0)
    result=dict(samples=len(truth),accuracy=float((truth==predicted).mean()),macro_f1=float(np.mean(f1)),
                precision=precision,recall=recall,confusion_matrix=confusion.tolist())
    if probabilities is not None:
        values=np.asarray(probabilities); ordered=np.sort(values,axis=1); scores=ordered[:,-1]; margins=scores-ordered[:,-2]
        accepted=(scores>top1)&(margins>margin)
        purity=[]; accepted_counts=[]
        for i in range(4):
            selected=accepted&(predicted==i); n=int(selected.sum()); accepted_counts.append(n)
            purity.append(float((truth[selected]==i).mean()) if n else None)
        result.update(coverage=float(accepted.mean()),selective_purity=purity,accepted_per_bin=accepted_counts,
                      high_confidence_errors=int((accepted&(truth!=predicted)).sum()),
                      confidence_percentiles=np.percentile(scores,[0,25,50,75,95,100]).tolist(),
                      margin_percentiles=np.percentile(margins,[0,25,50,75,95,100]).tolist(),
                      consensus_status="PER_IMAGE_ONLY; temporal consensus requires grouped physical frames")
    return result
