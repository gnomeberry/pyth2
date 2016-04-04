# encoding: utf-8
'''
Created on 2016/01/31

@author: oreyou
'''
from datetime import datetime
import math
import re
import cStringIO
import csv
import types


class ValueEstimator(object):
    '''
    文字列を受け入れられるか検証するもの
    '''
    def __init__(self, nullable = True):
        '''
        初期化
        
        @param nullable: Noneまたは空文字列を受け入れる場合は True
        '''
        self.nullable = nullable
    
    def check(self, strValue):
        '''
        文字列の検証を行う.
        このメソッドをオーバーライドしてはならない
        
        @param strValue: 対象の文字列
        @return: 対象の文字列を受け入れられる場合は Trueと等価な値、または受け入れられない場合は Falseと等価な値
        @raise: 対象の文字列を受け入れられない場合
        '''
        if not self.nullable and (strValue is None or len(strValue) == 0):
            return False
        return self._checkImpl(strValue)
    
    def _checkImpl(self, strValue):
        '''
        文字列の検証を行う.
        このメソッドに与えられる strValueは self#check() によって非 Noneな値であることが保障されている
        
        @param strValue: 対象の文字列(self.nullableが Trueと等価な場合は Noneまたは空文字列の場合がある)
        @return: 対象の文字列を受け入れられる場合は Trueと等価な値、または受け入れられない場合は Falseと等価な値
        @raise: 対象の文字列を受け入れられない場合
        '''
        raise ValueError("Cannot accept")
    
    @property
    def parser(self):
        """
        この検証するものが受理する文字列を受け取って値を返す関数を得る.
        得られた関数は次の操作を行うべき.
        <pre>
        def parser(s):
            return <parsed value> if <check s is valid string for this class> else None
        </pre>
        
        @return: 文字列を受け取って値を返す関数
        """
        raise NotImplemented
    
    @property
    def presenter(self):
        """
        値を受け取ってこの検証するものが受理する文字列を返す関数を得る.
        得られた関数は次の操作を行うべき.
        <pre>
        def presenter(v):
            return str(v) if <v is valid value for this class> else None
        </pre>
        
        @return: 値を受け取って文字列を返す関数
        """
        raise NotImplemented
    
    def __str__(self):
        return "%s" % self.__class__.__name__
    

class EstimationContext(object):
    '''
    ValueEstimatorの集合を持ち、それぞれの受け入れ状態を管理するもの
    '''
    def __init__(self, estimators):
        '''
        初期化
        
        @param estimators: ValueEstimatorの列挙可能なもの
        '''
        if not hasattr(estimators, "__iter__"):
            raise ValueError("%s is not an interable object" % estimators)
        for e in estimators:
            if not isinstance(e, ValueEstimator):
                raise ValueError("%s is not an estimator instance" % e)
        self.__estimators = list(estimators) # clone    
    
    def __str__(self):
        return "%s[%s]" % (self.__class__.__name__, self.__estimators)
    
    @property
    def availables(self):
        return tuple(self.__estimators)
    
    @property
    def feasible(self):
        return self.__estimators[0] if self.__estimators else None
            
    def update(self, strValue):
        '''
        この EstimationContextの持つ ValueEstimatorの集合に対して checkを行い、受け入れ状態を更新する
        
        @param strValue: 検証する文字列
        '''
        for est in self.__estimators:
            try:
                if not est.check(strValue):
                    self.__estimators.remove(est)
            except:
                self.__estimators.remove(est)

class StringEstimator(ValueEstimator):
    '''
    文字列を受け入れ可能なもの
    '''
    
    def __init__(self, nullable):
        super(StringEstimator, self).__init__(nullable)
    
    def _checkImpl(self, strValue):
        return True
    
    @property
    def parser(self):
        return lambda s: str(s) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: None if v is None else str(v)

class UnicodeEstimator(ValueEstimator):
    '''
    unicodeへ変換可能な文字列を受け入れるもの
    '''
    
    def __init__(self, strEncode, nullable):
        '''
        初期化
        
        @param strEncode: unicodeへ変換する際の文字エンコード
        @param nullable: nullを受け入れ可能な場合は True
        '''
        super(UnicodeEstimator, self).__init__(nullable)
        self.strEncode = strEncode
    
    def _checkImpl(self, strValue):
        unicode(strValue, self.strEncode)
        return True
    
    @property
    def parser(self):
        return lambda s: unicode(s, self.strEncode) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: str(v).decode(self.strEncode)

class RegexEstimator(ValueEstimator):
    '''
    正規表現にマッチするものを受け入れるもの
    '''
    
    def __init__(self, regex, nullable):
        '''
        初期化
        
        @param regex: 正規表現文字列
        @param nullable: nullを受け入れ可能な場合は True
        '''
        super(RegexEstimator, self).__init__(nullable)
        self.pattern = re.compile(regex)
    
    def _checkImpl(self, strValue):
        return self.pattern.match(strValue)
    
    @property
    def parser(self):
        return lambda s: self.pattern.match(s) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: str(v)

class RangedIntEstimator(ValueEstimator):
    '''
    整数の範囲にマッチする文字列を受け入れるもの
    '''
    
    def __init__(self, minInt, maxInt, nullable):
        '''
        初期化
        
        @param minInt: 範囲の最小値(含む)
        @param maxInt: 範囲の最大値(含む)
        @param nullable: nullを受け入れ可能な場合は True
        '''
        super(RangedIntEstimator, self).__init__(nullable)
        if not isinstance(minInt, (int, long)):
            raise ValueError("%s is not int or long" % minInt)
        if not isinstance(maxInt, (int, long)):
            raise ValueError("%s is not int or long" % maxInt)
        if not minInt <= maxInt:
            raise ValueError("min must be less than or equal to max: min=%d max=%d" % (minInt, maxInt))
        self.minInt = minInt
        self.maxInt = maxInt
        
    def _checkImpl(self, strValue):
        return self.minInt <= int(strValue) <= self.maxInt
    
    @property
    def parser(self):
        return lambda s: int(s) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: str(v) if isinstance(v, types.IntType) else None

class SignedBitwidthIntEstimator(RangedIntEstimator):
    """
    符号付整数を受け入れるもの
    """
    def __init__(self, bitWidth, nullable):
        bitWidth -= 1
        super(SignedBitwidthIntEstimator, self).__init__(-(2 ** bitWidth), 2 ** bitWidth - 1, nullable)

class UnsignedBitwidthIntEstimator(RangedIntEstimator):
    """
    符号なし整数を受け入れるもの
    """
    def __init__(self, bitWidth, nullable):
        super(UnsignedBitwidthIntEstimator, self).__init__(0, 2 ** bitWidth - 1, nullable)

class UInt32Estimator(UnsignedBitwidthIntEstimator):
    """
    32ビット整数を受け入れるもの
    """
    def __init__(self, nullable):
        super(UInt32Estimator, self).__init__(32, nullable)

class UInt64Estimator(UnsignedBitwidthIntEstimator):
    """
    64ビット整数を受け入れるもの
    """
    def __init__(self, nullable):
        super(UInt64Estimator, self).__init__(64, nullable)

class SInt32Estimator(SignedBitwidthIntEstimator):
    """
    2の補数表現の32ビット整数を受け入れるもの
    """
    def __init__(self, nullable):
        super(SInt32Estimator, self).__init__(32, nullable)

class SInt64Estimator(SignedBitwidthIntEstimator):
    """
    2の補数表現の64ビット整数を受け入れるもの
    """
    def __init__(self, nullable):
        super(SInt64Estimator, self).__init__(64, nullable)

class FloatClassEstimator(ValueEstimator):
    """
    浮動小数を受け入れるもの
    """
    def __init__(self, minValue, maxValue, includesNaN, nullable):
        super(FloatClassEstimator, self).__init__(nullable)
        if not isinstance(minValue, float):
            raise ValueError("%s is not float" % minValue)
        if not isinstance(maxValue, float):
            raise ValueError("%s is not float" % maxValue)
        if not includesNaN and any(map(math.isnan, (minValue, maxValue))):
            raise ValueError("min or max is NaN")
        elif not minValue <= maxValue:
            raise ValueError("min must be less than max: min=%f max=%f" % (minValue, maxValue))
        self.minValue = minValue
        self.maxValue = maxValue
        self.includesNaN = includesNaN
    
    def _checkImpl(self, strValue):
        strValue = strValue.lower()
        if strValue == "nan":
            return self.includesNaN
        elif strValue == "inf" or strValue == "+inf":
            return math.isinf(self.maxValue)
        elif strValue == "-inf":
            return math.isinf(self.minValue)
        else:
            return self.minValue <= float(strValue) <= self.maxValue
    
    @property
    def parser(self):
        return lambda s: float(s) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: str(v) if isinstance(v, types.FloatType) else None

class NotNaNFloatEstimator(FloatClassEstimator):
    def __init__(self, nullable):
        super(NotNaNFloatEstimator, self).__init__(float("-inf"), float("inf"), False, nullable)

class DatetimeClassEstimator(ValueEstimator):
    def __init__(self, strpFormat, nullable):
        super(DatetimeClassEstimator, self).__init__(nullable)
        self.strpFormat = strpFormat
        
    def _checkImpl(self, strValue):
        return datetime.strptime(strValue, self.strpFormat)
    
    @property
    def parser(self):
        return lambda s: datetime.strftime(s, self.strpFormat) if self.check(s) else None
    
    @property
    def presenter(self):
        return lambda v: v.strptime(self.strpFormat) if isinstance(v, datetime) else None

class RegexDatetimeEstimator(ValueEstimator):
    regexDatetimeParts = "year month day hour minute second microsecond tzinfo".split(" ")
    def __init__(self, regex = r"^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})$", regex_flags = 0, nullable = True):
        super(RegexDatetimeEstimator, self).__init__(nullable)
        self.regex = regex
        self._pattern = re.compile(regex, regex_flags)
    
    
    @staticmethod
    def parameterizedInitializer(parts = (("year", r"\d{4}"), ("month", r"\d{2}"), ("day", r"\d{2}"), ("hour", r"\d{2}"), ("minute", r"\d{2}"), ("second", r"\d{2}")), regex_flags = 0, nullable = True):
        regex = "^%s$" % "".join("(?P<%s>%s)" % tuple(part) for part in parts)
        return RegexDatetimeEstimator(regex, regex_flags, nullable)
        
    def _checkImpl(self, strValue):
        m = self._pattern.match(strValue)
        return m
    
    @property
    def parser(self):
        def _parser(s):
            m = self._pattern.match(s)
            if not m:
                return None
            md = m.groupdict()
            return datetime(**{k: int(md[k]) for k in RegexDatetimeEstimator.regexDatetimeParts if k in md})
        return _parser
    
#     @property
#     def presenter(self):
#         raise NotImplemented

class DisjunctionEstimator(ValueEstimator):
    
    def __init__(self, choice_estimators):
        if not hasattr(choice_estimators, "__iter__"):
            raise ValueError("%s is not an interable object" % choice_estimators)
        for e in estimators:
            if not isinstance(e, ValueEstimator):
                raise ValueError("%s is not an estimator instance" % e)
        self.__choices = list(choice_estimators) # clone
    
    @property
    def choices(self):
        return self.__choices
    
    def _checkImpl(self, strValue):
        self.__choices = filter(lambda e: e._checkImpl(strValue), self.__choices)
        

# STRP_DIRECTIVES = ["%a", "%A", "%b", "%B", "%c", "%d", "%f", "%H", "%I", "%j", "%m", "%M", "%p", "%S", "%U", "%w", "%W", "%x", "%X", "%y", "%Y", "%z", "%Z"]
# class RegexDatetimeClassEstimator(ValueEstimator):
#     def __init__(self, regexStrpFormat, nullable):
#         """
#         (?P<%Y>\d+)?_
#         
#         %a     ロケールの短縮された曜日名を表示します
#         %A     ロケールの曜日名を表示します
#         %b     ロケールの短縮された月名を表示します
#         %B     ロケールの月名を表示します
#         %c     ロケールの日時を適切な形式で表示します
#         %d     月中の日にちを10進表記した文字列 [01,31] を表示します
#         %f     マイクロ秒を10進表記した文字列 [000000,999999] を表示します (左側から0埋めされます)     (1)
#         %H     時 (24時間表記) を10進表記した文字列 [00,23] を表示します
#         %I     時 (12時間表記) を10進表記した文字列 [01,12] を表示します
#         %j     年中の日にちを10進表記した文字列 [001,366] を表示します
#         %m     月を10進表記した文字列 [01,12] を表示します
#         %M     分を10進表記した文字列 [00,59] を表示します
#         %p     ロケールの AM もしくは PM を表示します     (2)
#         %S     秒を10進表記した文字列 [00,61] を表示します     (3)
#         %U     年中の週番号 (週の始まりは日曜日とする) を10進表記した文字列 [00,53] を表示します新年の最初の日曜日に先立つ日は 0週に属するとします     (4)
#         %w     曜日を10進表記した文字列 [0(日曜日),6] を表示します
#         %W     年中の週番号 (週の始まりは月曜日とする) を10進表記した文字列 [00,53] を表示します新年の最初の月曜日に先立つ日は 0週に属するとします     (4)
#         %x     ロケールの日付を適切な形式で表示します
#         %X     ロケールの時間を適切な形式で表示します
#         %y     世紀なしの年(下2桁)を10進表記した文字列 [00,99] を表示します
#         %Y     世紀ありの年を10進表記した文字列を表示します
#         %z     UTCオフセットを +HHMM もしくは -HHMM の形式で表示します (オブジェクトがnaiveであれば空文字列)     (5)
#         %Z     タイムゾーンの名前を表示します (オブジェクトがnaiveであれば空文字列)
#         """
#         
#         super(RegexDatetimeClassEstimator, self).__init__(nullable)
#         self.pattern = re.compile(regexStrpFormat)
#         self.indexToGroupName = [None] * self.pattern.groups
#         for name, idx in self.pattern.groupindex.items():
#             self.indexToGroupName[idx] = name
#     
#     def _checkImpl(self, strValue):
#         m = self.pattern.match()
#         if m:
#             

if __name__ == "__main__":
    estimators = (
                  RegexDatetimeEstimator.parameterizedInitializer(nullable = False),
                  SInt32Estimator(False),
                  NotNaNFloatEstimator(False),
                  StringEstimator(False))
    ecs = [
           EstimationContext(estimators), 
           EstimationContext(estimators), 
           EstimationContext(estimators),
           EstimationContext(estimators)]
    csv_data = \
"""1.1,20,3.1,20160404010101
4,5,6,20160404010102
7,8,c,20160404010103"""
    sio = cStringIO.StringIO(csv_data)
    r = csv.reader(sio)
    for row in r:
        for e, c in zip(ecs, row):
            e.update(c)
            print e
    print [ec.feasible for ec in ecs]
    print ecs[3].feasible.parser("20160404010102")

    