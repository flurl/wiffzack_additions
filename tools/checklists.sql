USE [wiffzack]
GO

SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [dbo].[checklist_master](
	[chm_id] [int] IDENTITY(1,1) NOT NULL,
	[chm_name] [varchar](255) NOT NULL,
	[chm_category] [varchar](255) NOT NULL,
 CONSTRAINT [PK_checklist_master] PRIMARY KEY CLUSTERED 
(
	[chm_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO





CREATE TABLE [dbo].[checklist_questions](
	[chq_id] [int] IDENTITY(1,1) NOT NULL,
	[chq_text] [varchar](max) NOT NULL,
	[chq_order] [int] NOT NULL,
	[chq_chmid] [int] NOT NULL,
 CONSTRAINT [PK_checklist_questions] PRIMARY KEY CLUSTERED 
(
	[chq_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO

ALTER TABLE [dbo].[checklist_questions]  WITH CHECK ADD  CONSTRAINT [FK_checklist_questions_checklist_master] FOREIGN KEY([chq_chmid])
REFERENCES [dbo].[checklist_master] ([chm_id])
GO

ALTER TABLE [dbo].[checklist_questions] CHECK CONSTRAINT [FK_checklist_questions_checklist_master]
GO





CREATE TABLE [dbo].[checklists](
	[chk_id] [int] IDENTITY(1,1) NOT NULL,
	[chk_datum] [datetime] NOT NULL,
	[chk_completed] [bit] NOT NULL,
	[chk_master_name] [varchar](255) NOT NULL,
 CONSTRAINT [PK_checklists] PRIMARY KEY CLUSTERED 
(
	[chk_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[checklists] ADD  CONSTRAINT [DF_checklists_chk_completed]  DEFAULT ((0)) FOR [chk_completed]
GO




CREATE TABLE [dbo].[checklist_answers](
	[cha_id] [int] IDENTITY(1,1) NOT NULL,
	[cha_chkid] [int] NOT NULL,
	[cha_question_text] [varchar](max) NOT NULL,
	[cha_choice] [bit] NULL,
	[cha_order] [int] NOT NULL,
 CONSTRAINT [PK_checklist_answers] PRIMARY KEY CLUSTERED 
(
	[cha_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

ALTER TABLE [dbo].[checklist_answers] ADD  DEFAULT ((0)) FOR [cha_order]
GO

ALTER TABLE [dbo].[checklist_answers]  WITH CHECK ADD  CONSTRAINT [FK_checklist_answers_checklists] FOREIGN KEY([cha_chkid])
REFERENCES [dbo].[checklists] ([chk_id])
GO

ALTER TABLE [dbo].[checklist_answers] CHECK CONSTRAINT [FK_checklist_answers_checklists]
GO
