from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
from typing import Union
from scraper_service.client.schemas.base import ResponseBaseModel


class CompanyRequest(ResponseBaseModel):
    username: str

class ProfileRequest(CompanyRequest):
    pass
class Image(ResponseBaseModel):
    url: str
    width: int
    height: int
    
class Location(ResponseBaseModel):
    geographicArea: str
    country: str
    city: str
    line1: str
    postalCode: str | None = None
    headquarter: bool | None = None

class CallToActionMessage(ResponseBaseModel):
    textDirection: Optional[str] = ""
    text: Optional[str] = ""
    
class CallToAction(ResponseBaseModel):
    type: Optional[str] = None  # instead of callToActionType
    visible: Optional[bool] = None
    callToActionMessage: Optional[CallToActionMessage] = None
    url: Optional[str] = None

class MoneyRaised(ResponseBaseModel):
    currencyCode: str
    amount: str

class LeadInvestor(ResponseBaseModel):
    name: str
    investorCrunchbaseUrl: str


class AnnouncedOn(ResponseBaseModel):
    month: int
    day: int
    year: int


class LastFundingRound(ResponseBaseModel):
    investorsCrunchbaseUrl: str
    leadInvestors: list[LeadInvestor]
    fundingRoundCrunchbaseUrl: str
    fundingType: str
    moneyRaised: MoneyRaised
    numOtherInvestors: int
    announcedOn: AnnouncedOn

class FundingData(ResponseBaseModel):
    updatedAt: str
    updatedDate: str
    numFundingRounds: int
    lastFundingRound: LastFundingRound

class CompanyData(ResponseBaseModel):
    id: str
    name: str
    universalName: str
    linkedinUrl: str
    tagline: str
    description: str
    type: str
    phone: str
    Images: dict[str, str]
    isClaimable: bool
    backgroundCoverImages: list[Image]
    logos: list[Image]
    staffCount: int
    headquarter: Optional[Location] = None
    locations: Optional[list[Location]] = None
    industries: list[str]
    specialities: list[str]
    website: str
    founded: Union[str, Dict[str, Any], None] = None
    callToAction: CallToAction
    followerCount: int
    staffCountRange: str
    crunchbaseUrl: str
    fundingData: Optional[FundingData] = None


class CompanyResponse(ResponseBaseModel):
    success: bool
    message: str
    data: CompanyData






class Date(ResponseBaseModel):
    year: int
    month: int
    day: int

class Education(ResponseBaseModel):
    start: Date
    end: Date
    fieldOfStudy: str
    degree: str
    grade: str
    schoolName: str
    description: str
    activities: str
    url: str
    schoolId: str
    logo: List[Image]

class Position(ResponseBaseModel):
    companyId: int
    companyName: str
    companyUsername: str
    companyURL: str
    companyLogo: Optional[str]
    companyIndustry: str
    companyStaffCountRange: str
    title: str
    multiLocaleTitle: Optional[Dict[str, str]]
    multiLocaleCompanyName: Optional[Dict[str, str]]
    location: str
    description: str
    employmentType: str
    start: Date
    end: Date

class Skill(BaseModel):
    name: str
    passedSkillAssessment: bool
    endorsementsCount: Optional[int] = 0 

class Geo(ResponseBaseModel):
    country: str
    city: str
    full: str
    countryCode: str

class Locale(ResponseBaseModel):
    country: str
    language: str

class ProfileResponse(ResponseBaseModel):
    id: int
    urn: str
    username: str
    firstName: str
    lastName: str
    isTopVoice: Optional[bool] = False  # <-- fix here
    isCreator: Optional[bool] = False 
    isPremium: bool
    profilePicture: Optional[str]
    backgroundImage: Optional[List[Image]]
    summary: str
    headline: str
    geo: Geo
    educations: List[Education]
    position: List[Position]
    fullPositions: Optional[List[Position]]
    skills: List[Skill]
    projects: Dict[str, Any]
    supportedLocales: List[Locale]
    multiLocaleFirstName: Dict[str, str]
    multiLocaleLastName: Dict[str, str]
    multiLocaleHeadline: Dict[str, str]
