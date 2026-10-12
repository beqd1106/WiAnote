import sys,re,subprocess
src_new=open(sys.argv[1],encoding='utf-8').read()   # WiAnote patched StudyStore
dst=sys.argv[2]; s=open(dst,encoding='utf-8').read()
a=src_new.index('    /// 1問でも解いたことのある問題ID')
b=src_new.index('    func studyDays() -> Set<Date> {')
tail=src_new[src_new.index('// MARK: - 日ごとの学習記録'):]
assert 'func answeredQuestionIds' not in s
anchor='    func studyDays() -> Set<Date> {'
assert s.count(anchor)==1
s=s.replace(anchor, src_new[a:b]+anchor)
s=s.rstrip('\n')+'\n\n'+tail
open(dst,'w',encoding='utf-8').write(s)
